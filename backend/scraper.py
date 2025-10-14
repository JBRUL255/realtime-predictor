# backend/scraper.py
from playwright.sync_api import sync_playwright

def scrape_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        title = page.title()
        browser.close()
    return {"url": url, "title": title}
