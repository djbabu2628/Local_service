import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ FIXED DATABASE URL
DATABASE_URL = os.getenv("DATABASE_URL")

DEFAULT_PLATFORM_FEE = 49.0
DEFAULT_SERVICE_CHARGES = {
    'Plumber': 399.0,
    'Electrician': 449.0,
    'Mechanic': 549.0,
    'AC Repair': 699.0,
    'Carpenter': 499.0,
    'Handyman': 349.0,
}


class DBWrapper:
    def __init__(self, conn):
        self.conn = conn
        
    def execute(self, query, params=None):
        q = query.replace('?', '%s')
        
        is_insert = q.strip().upper().startswith("INSERT INTO")
        if is_insert and "RETURNING " not in q.upper():
            q += " RETURNING id"
            
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        if params:
            cursor.execute(q, params)
        else:
            cursor.execute(q)
            
        if is_insert:
            try:
                row = cursor.fetchone()
                if row and 'id' in row:
                    cursor.lastrowid = row['id']
            except Exception:
                pass
                
        return cursor
        
    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
        
    def cursor(self):
        return self.conn.cursor()


# ✅ PostgreSQL Connection
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return DBWrapper(conn)


# ✅ INIT DATABASE (PostgreSQL)
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        profile_photo TEXT,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # PROVIDERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS providers (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL,
        service_type TEXT NOT NULL,
        availability TEXT DEFAULT 'AVAILABLE',
        address TEXT,
        latitude REAL,
        longitude REAL,
        base_charge REAL DEFAULT 0,
        platform_fee REAL DEFAULT 49,
        rating REAL DEFAULT 4.5,
        total_jobs INTEGER DEFAULT 0,
        profile_photo TEXT,
        experience TEXT,
        charge_type TEXT DEFAULT 'per_visit',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # SERVICE REQUESTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_requests (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        provider_id INTEGER REFERENCES providers(id) ON DELETE SET NULL,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        service_type TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'PENDING',
        scheduled_date DATE,
        scheduled_time TIME,
        address TEXT,
        user_latitude REAL,
        user_longitude REAL,
        payment_status TEXT DEFAULT 'PENDING',
        service_amount REAL DEFAULT 0,
        platform_fee REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        accepted_at TIMESTAMP,
        payment_method TEXT DEFAULT 'ONLINE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """)

    # PAYMENTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        booking_id INTEGER UNIQUE REFERENCES service_requests(id) ON DELETE CASCADE,
        provider_id INTEGER REFERENCES providers(id) ON DELETE SET NULL,
        gateway TEXT DEFAULT 'RAZORPAY',
        razorpay_order_id TEXT,
        razorpay_payment_id TEXT,
        razorpay_signature TEXT,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        service_charge REAL,
        platform_fee REAL,
        status TEXT DEFAULT 'CREATED',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ PostgreSQL Database Initialized")


# ✅ SEED DEFAULT VALUES
def seed_defaults():
    conn = get_db()
    cursor = conn.cursor()

    for service, charge in DEFAULT_SERVICE_CHARGES.items():
        cursor.execute("""
        UPDATE providers
        SET base_charge = %s
        WHERE service_type = %s
        AND (base_charge IS NULL OR base_charge <= 0)
        """, (charge, service))

    cursor.execute("""
    UPDATE providers
    SET platform_fee = %s
    WHERE platform_fee IS NULL OR platform_fee <= 0
    """, (DEFAULT_PLATFORM_FEE,))

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_defaults()