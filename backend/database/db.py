# database/db.py — SQLite connection + table init
import sqlite3
import os

# Railway pe /app/database/ folder mein DB store hoga
# Local pe bhi same kaam karega
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR   = os.path.join(BASE_DIR, 'database')
DB_PATH  = os.path.join(DB_DIR, 'local_service.db')

# Ensure database folder exists (Railway pe zaruri hai)
os.makedirs(DB_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        email      TEXT NOT NULL UNIQUE,
        password   TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS providers (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL,
        email        TEXT NOT NULL UNIQUE,
        phone        TEXT NOT NULL,
        password     TEXT NOT NULL,
        service_type TEXT NOT NULL,
        availability TEXT DEFAULT 'AVAILABLE',
        created_at   TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS service_requests (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        phone         TEXT NOT NULL,
        service_type  TEXT NOT NULL,
        description   TEXT NOT NULL,
        status        TEXT DEFAULT 'PENDING',
        provider_id   INTEGER DEFAULT NULL,
        created_at    TEXT DEFAULT (datetime('now','localtime')),
        completed_at  TEXT DEFAULT NULL,
        FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
        FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    conn.close()
    print("[DB] Database initialised at:", DB_PATH)
