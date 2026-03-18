"""
routes/providers.py — Provider Routes
POST /api/provider/register
POST /api/provider/login
GET  /api/provider/stats/<id>
"""

import hashlib
from flask import Blueprint, request, jsonify
from database.db import get_db

providers_bp = Blueprint('providers', __name__)


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Register ──────────────────────────────────────────────────
@providers_bp.route('/api/provider/register', methods=['POST'])
def provider_register():
    data         = request.get_json(silent=True) or {}
    name         = data.get('name', '').strip()
    email        = data.get('email', '').strip().lower()
    phone        = data.get('phone', '').strip()
    password     = data.get('password', '')
    service_type = data.get('service_type', '').strip()

    if not all([name, email, phone, password, service_type]):
        return jsonify(success=False, message='All fields are required.'), 400

    try:
        db = get_db()
        existing = db.execute('SELECT id FROM providers WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify(success=False, message='This email is already registered.'), 409

        cursor = db.execute(
            """INSERT INTO providers (name, email, phone, password, service_type, availability)
               VALUES (?, ?, ?, ?, ?, 'AVAILABLE')""",
            (name, email, phone, hash_pw(password), service_type)
        )
        db.commit()
        pid = cursor.lastrowid
        return jsonify(
            success=True,
            message='Provider account created successfully!',
            provider={'id': pid, 'name': name, 'email': email,
                      'service_type': service_type, 'availability': 'AVAILABLE'}
        ), 201
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()


# ── Login ─────────────────────────────────────────────────────
@providers_bp.route('/api/provider/login', methods=['POST'])
def provider_login():
    data     = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([email, password]):
        return jsonify(success=False, message='Email and password are required.'), 400

    try:
        db  = get_db()
        row = db.execute(
            'SELECT id, name, email, service_type, availability FROM providers WHERE email = ? AND password = ?',
            (email, hash_pw(password))
        ).fetchone()

        if not row:
            return jsonify(success=False, message='Invalid email or password.'), 401

        return jsonify(
            success=True,
            message='Login successful.',
            provider=dict(row)
        )
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()


# ── Provider Stats ────────────────────────────────────────────
@providers_bp.route('/api/provider/stats/<int:provider_id>', methods=['GET'])
def provider_stats(provider_id):
    try:
        db = get_db()

        completed = db.execute(
            "SELECT COUNT(*) AS cnt FROM service_requests WHERE provider_id = ? AND status = 'COMPLETED'",
            (provider_id,)
        ).fetchone()['cnt']

        active_count = db.execute(
            "SELECT COUNT(*) AS cnt FROM service_requests WHERE provider_id = ? AND status = 'ASSIGNED'",
            (provider_id,)
        ).fetchone()['cnt']

        active_job = db.execute(
            """SELECT id, customer_name, phone, service_type, description, created_at
               FROM service_requests
               WHERE provider_id = ? AND status = 'ASSIGNED'
               ORDER BY created_at DESC LIMIT 1""",
            (provider_id,)
        ).fetchone()

        return jsonify(
            success=True,
            stats={
                'completed_jobs': completed,
                'active_jobs':    active_count,
                'active_job':     dict(active_job) if active_job else None
            }
        )
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()
