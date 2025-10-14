# backend/scraper.py
import os, time, json, logging, re
from datetime import datetime
from .db import SessionLocal, Round
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("aviator-scraper")
logger.setLevel(logging.INFO)

# Environment-controlled settings
AVIATOR_PAGE_URL = os.getenv("AVIATOR_PAGE_URL", "")  # e.g. https://www.betika.com/en-ke/aviator
STORAGE_STATE_PATH = os.getenv("PLAYWRIGHT_STORAGE_STATE", "/tmp/playwright_storage.json")
HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "1") != "0"
LOGIN_EMAIL = os.getenv("PLAYWRIGHT_LOGIN_EMAIL", "")
LOGIN_PASSWORD = os.getenv("PLAYWRIGHT_LOGIN_PASSWORD", "")
SCRAPE_POLL_SECONDS = int(os.getenv("SCRAPER_POLL_INTERVAL", "1"))
DOM_MULTIPLIER_SELECTORS = [
    # common selectors — adjust as needed
    ".multiplier", ".crash-value", ".round-multiplier", ".value"
]

def save_round(multiplier, round_id=None, raw=None):
    try:
        db = SessionLocal()
        r = Round(round_id=str(round_id) if round_id else None,
                  multiplier=float(multiplier) if multiplier is not None else None,
                  ts=datetime.utcnow(),
                  raw=raw)
        db.add(r)
        db.commit()
        db.close()
        logger.info(f"[DB] saved round round_id={round_id} mult={multiplier}")
    except Exception:
        logger.exception("Failed to save round")

def try_login_and_save_state(page):
    """
    Attempt a scripted login if env credentials are provided.
    This function is site-specific. You may need to modify selectors to match Betika.
    """
    if not LOGIN_EMAIL or not LOGIN_PASSWORD:
        logger.info("No login credentials provided; skipping scripted login.")
        return False

    logger.info("Attempting scripted login...")
    try:
        # NOTE: These selectors are examples; you must adapt to actual site fields.
        # Wait for login form
        page.wait_for_selector("input[type=email], input[name=email], input#email", timeout=10000)
        # Attempt to fill common fields
        if page.query_selector("input[type=email]"):
            page.fill("input[type=email]", LOGIN_EMAIL)
        elif page.query_selector("input[name=email]"):
            page.fill("input[name=email]", LOGIN_EMAIL)

        if page.query_selector("input[type=password]"):
            page.fill("input[type=password]", LOGIN_PASSWORD)
        elif page.query_selector("input[name=password]"):
            page.fill("input[name=password]", LOGIN_PASSWORD)

        # click first submit button found
        btn = page.query_selector("button[type=submit], button.login, button#login")
        if btn:
            btn.click()
            # wait for navigation or auth indicator
            page.wait_for_timeout(5000)
        else:
            logger.warning("No submit button found on login form, login may fail.")
        # After login save storage state
        page.context.storage_state(path=STORAGE_STATE_PATH)
        logger.info(f"Saved storage state to {STORAGE_STATE_PATH}")
        return True
    except Exception:
        logger.exception("Scripted login attempt failed")
        return False

def install_hooks_in_page(page):
    """
    Inject JS into the page to hook WebSocket messages and fetch/XHR responses.
    Hook forwards events via window.__AVIATOR_COLLECTOR__ array which we poll from Python.
    """
    js = r"""(function(){
  if (window.__AVIATOR_COLLECTOR__) return;
  window.__AVIATOR_COLLECTOR__ = [];
  const pushToCollector = (obj) => {
    try { window.__AVIATOR_COLLECTOR__.push(obj); }
    catch(e){}
  };

  // Hook WebSocket
  const OriginalWebSocket = window.WebSocket;
  function HookedWebSocket(url, protocols) {
    const ws = protocols ? new OriginalWebSocket(url, protocols) : new OriginalWebSocket(url);
    ws.addEventListener('message', (evt) => {
      try {
        let data = evt.data;
        let parsed = null;
        try { parsed = JSON.parse(data); } catch(e) {
          const idx = data.indexOf('[');
          if (idx !== -1) {
            try { parsed = JSON.parse(data.slice(idx)); } catch(e2){}
          }
        }
        const out = {source: 'ws', url: url, raw: data, parsed: parsed};
        pushToCollector(out);
      } catch(e) { }
    });
    return ws;
  }
  HookedWebSocket.prototype = OriginalWebSocket.prototype;
  window.WebSocket = HookedWebSocket;

  // Hook fetch/XHR
  const origFetch = window.fetch;
  window.fetch = function(){
    return origFetch.apply(this, arguments).then(async (resp) => {
      try {
        const ct = resp.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
          const clone = resp.clone();
          const data = await clone.json().catch(()=>null);
          if (data) {
            pushToCollector({source:'fetch', raw: JSON.stringify(data), parsed: data});
          }
        }
      } catch(e){}
      return resp;
    });
  };

  console.log('[collector] hooks installed');
})();"""
    try:
        page.add_init_script(js)
        page.evaluate(js)
    except PlaywrightTimeoutError:
        logger.exception("JS hook injection timed out")

def parse_collected_item(item):
    """
    Try to extract multiplier and round_id from the collected item (parsed or raw).
    """
    mult = None
    rid = None
    raw = None
    try:
        raw = item.get("raw")
        parsed = item.get("parsed")
        if parsed:
            # try common shapes
            if isinstance(parsed, dict):
                # direct fields
                for key in ("multiplier","crash","value","mult"):
                    if key in parsed:
                        try: mult = float(parsed[key]); break
                        except: pass
                # nested: rounds array
                if mult is None and "rounds" in parsed and isinstance(parsed["rounds"], list):
                    last = parsed["rounds"][-1]
                    if isinstance(last, dict):
                        mult = float(last.get("multiplier") or last.get("crash") or last.get("value") or 0)
                        rid = last.get("round_id") or last.get("id")
                # socket.io arrays like ["round_end", {...}]
                if mult is None:
                    # if parsed is list
                    if isinstance(parsed, list) and len(parsed) > 1 and isinstance(parsed[1], dict):
                        d = parsed[1]
                        if isinstance(d, dict):
                            for key in ("multiplier","crash","value"):
                                if key in d:
                                    try: mult = float(d[key]); break
                                    except: pass
                            rid = d.get("round_id") or d.get("id") or rid
            elif isinstance(parsed, list):
                # similar attempt
                for el in parsed[::-1]:
                    if isinstance(el, dict):
                        for key in ("multiplier","crash","value"):
                            if key in el:
                                try: mult = float(el[key]); break
                                except: pass
                        rid = el.get("round_id") or el.get("id") or rid
        else:
            # raw fallback: regex for x2.35 or 2.35x
            s = str(raw)
            m = re.search(r'(\d+\.\d+|\d+)\s*[xX]?', s)
            if m:
                try: mult = float(m.group(1))
                except: pass
    except Exception:
        logger.exception("parse error")
    return mult, rid, raw

def start_playwright_collector(page_url):
    """
    Main loop: launch Playwright, open page (with storage state if available),
    inject hooks, then poll page.__AVIATOR_COLLECTOR__ and DOM for multiplier until process killed.
    """
    logger.info("Starting Playwright collector...")
    while True:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=HEADLESS, args=["--no-sandbox","--disable-setuid-sandbox"])
                context_args = {}
                if os.path.exists(STORAGE_STATE_PATH):
                    context_args["storage_state"] = STORAGE_STATE_PATH
                    logger.info(f"Using storage state: {STORAGE_STATE_PATH}")
                else:
                    # create empty context; we'll attempt scripted login
                    logger.info("No storage state file found; starting fresh context")
                context = browser.new_context(**context_args)
                page = context.new_page()
                logger.info(f"Navigating to {page_url}")
                page.goto(page_url, wait_until="networkidle", timeout=60000)

                # If not logged in and credentials provided, attempt login and save storage
                if not os.path.exists(STORAGE_STATE_PATH):
                    ok = try_login_and_save_state(page)
                    if ok:
                        page.context.storage_state(path=STORAGE_STATE_PATH)
                        logger.info("Login+storage_state saved")

                # install hooks
                install_hooks_in_page(page)

                last_seen_multiplier = None
                # DOM polling approach — attempt to find multiplier elements
                while True:
                    try:
                        # Poll page.__AVIATOR_COLLECTOR__ items
                        items = page.evaluate("() => window.__AVIATOR_COLLECTOR__ ? window.__AVIATOR_COLLECTOR__.splice(0) : []")
                        if items and isinstance(items, list):
                            for it in items:
                                mult, rid, raw = parse_collected_item(it)
                                if mult is not None:
                                    save_round(multiplier=mult, round_id=rid, raw=raw)
                        # DOM polling: check common selectors
                        for sel in ["div.multiplier","span.multiplier",".crash-value",".round-multiplier",".value"]:
                            try:
                                text = page.evaluate(f"""() => {{
                                    const el = document.querySelector("{sel}");
                                    return el ? el.innerText.trim() : null;
                                }}""")
                            except Exception:
                                text = None
                            if text:
                                # extract number
                                m = re.search(r'(\d+\.\d+|\d+)', text)
                                if m:
                                    cur = float(m.group(1))
                                    if last_seen_multiplier is None or cur != last_seen_multiplier:
                                        last_seen_multiplier = cur
                                        # if multiplier is >1.0 treat as live round update
                                        save_round(multiplier=cur, round_id=None, raw=f"dom:{sel}:{text}")
                                break
                        time.sleep(SCRAPE_POLL_SECONDS)
                    except PlaywrightTimeoutError:
                        logger.warning("Playwright timeout inside polling loop; continuing")
                        time.sleep(1)
                    except Exception:
                        logger.exception("Error in inner polling loop; continue")
                        time.sleep(1)
        except Exception:
            logger.exception("Playwright collector crashed; restarting in 5s")
            time.sleep(5)
            continue
