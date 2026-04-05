"""
routes/auth.py — User Authentication Routes
POST /api/user/register
POST /api/user/login

⚠️ SECURITY NOTE:
Passwords are hashed with plain SHA-256 (no salt). This is acceptable
for localhost development but NOT safe for production. For production,
replace hash_pw() with werkzeug.security.generate_password_hash() and
check_password_hash() which use PBKDF2 with a random salt.
"""

import hashlib
from flask import Blueprint, request, jsonify
from database.db import get_db

auth_bp = Blueprint('auth', __name__)


# ⚠️ Plain SHA-256 — upgrade to werkzeug.security.generate_password_hash for production
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── Register ──────────────────────────────────────────────────
@auth_bp.route('/api/user/register', methods=['POST'])
def user_register():
    data = request.get_json(silent=True) or {}
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([name, email, password]):
        return jsonify(success=False, message='All fields are required.'), 400
    if len(password) < 6:
        return jsonify(success=False, message='Password must be at least 6 characters.'), 400

    try:
        db = get_db()
        # Check duplicate
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify(success=False, message='This email is already registered.'), 409

        cursor = db.execute(
            'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
            (name, email, hash_pw(password))
        )
        db.commit()
        return jsonify(
            success=True,
            message='Account created successfully!',
            user={'id': cursor.lastrowid, 'name': name, 'email': email}
        ), 201
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()


# ── Login ─────────────────────────────────────────────────────
@auth_bp.route('/api/user/login', methods=['POST'])
def user_login():
    data = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([email, password]):
        return jsonify(success=False, message='Email and password are required.'), 400

    try:
        db   = get_db()
        user = db.execute(
            'SELECT id, name, email FROM users WHERE email = ? AND password = ?',
            (email, hash_pw(password))
        ).fetchone()

        if not user:
            return jsonify(success=False, message='Invalid email or password.'), 401

        return jsonify(
            success=True,
            message='Login successful.',
            user={'id': user['id'], 'name': user['name'], 'email': user['email']}
        )
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()
