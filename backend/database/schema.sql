-- ============================================================
--  LSES — SQLite Schema
--  Tables are also auto-created by db.py at startup.
--  This file serves as the canonical reference for the schema.
-- ============================================================

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
