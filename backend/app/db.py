import sqlite3
from contextlib import contextmanager

DB_NAME = "aviator.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            result REAL
        )
        """)
        conn.commit()

def save_prediction(result: float):
    from datetime import datetime
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO predictions (timestamp, result) VALUES (?, ?)",
            (datetime.now().isoformat(), result)
        )
        conn.commit()

def fetch_all_predictions():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions ORDER BY id DESC")
        return cursor.fetchall()

