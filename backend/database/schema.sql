-- ============================================================
--  LSES — MySQL Schema (use this if you prefer MySQL over SQLite)
--  For SQLite: tables are auto-created by db.py
-- ============================================================
CREATE DATABASE IF NOT EXISTS local_service_emergency;
USE local_service_emergency;

CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   VARCHAR(64)  NOT NULL,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS providers (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(150) NOT NULL UNIQUE,
    phone        VARCHAR(20)  NOT NULL,
    password     VARCHAR(64)  NOT NULL,
    service_type VARCHAR(50)  NOT NULL,
    availability ENUM('AVAILABLE','BUSY') DEFAULT 'AVAILABLE',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS service_requests (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT          NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    phone         VARCHAR(20)  NOT NULL,
    service_type  VARCHAR(50)  NOT NULL,
    description   TEXT         NOT NULL,
    status        ENUM('PENDING','ASSIGNED','COMPLETED') DEFAULT 'PENDING',
    provider_id   INT          DEFAULT NULL,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    completed_at  TIMESTAMP    DEFAULT NULL,
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE SET NULL
);
