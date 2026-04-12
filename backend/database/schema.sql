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
    address      TEXT,
    latitude     REAL,
    longitude    REAL,
    base_charge  REAL DEFAULT 0,
    platform_fee REAL DEFAULT 49,
    rating       REAL DEFAULT 4.5,
    total_jobs   INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT (datetime('now','localtime')),
    updated_at   TEXT
);

CREATE TABLE IF NOT EXISTS service_requests (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    customer_name  TEXT NOT NULL,
    phone          TEXT NOT NULL,
    service_type   TEXT NOT NULL,
    description    TEXT NOT NULL,
    status         TEXT DEFAULT 'PENDING',
    provider_id    INTEGER DEFAULT NULL,
    scheduled_date TEXT,
    scheduled_time TEXT,
    address        TEXT,
    user_latitude  REAL,
    user_longitude REAL,
    payment_status TEXT DEFAULT 'PENDING',
    service_amount REAL DEFAULT 0,
    platform_fee   REAL DEFAULT 0,
    total_amount   REAL DEFAULT 0,
    created_at     TEXT DEFAULT (datetime('now','localtime')),
    accepted_at    TEXT DEFAULT NULL,
    completed_at   TEXT DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id          INTEGER NOT NULL UNIQUE,
    provider_id         INTEGER DEFAULT NULL,
    gateway             TEXT NOT NULL DEFAULT 'RAZORPAY',
    razorpay_order_id   TEXT,
    razorpay_payment_id TEXT,
    razorpay_signature  TEXT,
    amount              REAL NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'INR',
    service_charge      REAL NOT NULL,
    platform_fee        REAL NOT NULL,
    status              TEXT NOT NULL DEFAULT 'CREATED',
    error_message       TEXT,
    created_at          TEXT DEFAULT (datetime('now','localtime')),
    updated_at          TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (booking_id) REFERENCES service_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE SET NULL
);
