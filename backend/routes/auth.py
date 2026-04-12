"""
routes/auth.py — User Authentication Routes
POST /api/user/register
POST /api/user/login
PUT  /api/user/<id>/profile

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


def parse_float(value):
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ── Register ──────────────────────────────────────────────────
@auth_bp.route('/api/user/register', methods=['POST'])
def user_register():
    data = request.get_json(silent=True) or {}
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    phone    = data.get('phone', '').strip()
    address  = data.get('address', '').strip()
    latitude = parse_float(data.get('latitude'))
    longitude = parse_float(data.get('longitude'))
    profile_photo = data.get('profile_photo', '').strip()

    if not all([name, email, password]):
        return jsonify(success=False, message='Name, email, and password are required.'), 400
    if len(password) < 6:
        return jsonify(success=False, message='Password must be at least 6 characters.'), 400

    db = None
    try:
        db = get_db()
        # Check duplicate
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify(success=False, message='This email is already registered.'), 409

        cursor = db.execute(
            '''INSERT INTO users (name, email, password, phone, address, latitude, longitude, profile_photo, role)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'user')''',
            (name, email, hash_pw(password), phone, address, latitude, longitude, profile_photo)
        )
        db.commit()
        user_id = cursor.lastrowid
        return jsonify(
            success=True,
            message='Account created successfully!',
            user={
                'id': user_id, 'name': name, 'email': email,
                'phone': phone, 'address': address,
                'latitude': latitude, 'longitude': longitude,
                'profile_photo': profile_photo, 'role': 'user'
            }
        ), 201
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        if db:
            db.close()


# ── Login ─────────────────────────────────────────────────────
@auth_bp.route('/api/user/login', methods=['POST'])
def user_login():
    data = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([email, password]):
        return jsonify(success=False, message='Email and password are required.'), 400

    db = None
    try:
        db   = get_db()
        user = db.execute(
            '''SELECT id, name, email, phone, address, latitude, longitude, profile_photo, role
               FROM users WHERE email = ? AND password = ?''',
            (email, hash_pw(password))
        ).fetchone()

        if not user:
            return jsonify(success=False, message='Invalid email or password.'), 401

        return jsonify(
            success=True,
            message='Login successful.',
            user={
                'id': user['id'], 'name': user['name'], 'email': user['email'],
                'phone': user['phone'] or '', 'address': user['address'] or '',
                'latitude': user['latitude'], 'longitude': user['longitude'],
                'profile_photo': user['profile_photo'] or '', 'role': user['role'] or 'user'
            }
        )
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        if db:
            db.close()


# ── Update User Profile ──────────────────────────────────────
@auth_bp.route('/api/user/<int:user_id>/profile', methods=['PUT'])
def update_user_profile(user_id):
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    latitude = parse_float(data.get('latitude'))
    longitude = parse_float(data.get('longitude'))
    profile_photo = data.get('profile_photo', '').strip()

    db = None
    try:
        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
        if not existing:
            return jsonify(success=False, message='User not found.'), 404

        db.execute(
            '''UPDATE users SET phone = ?, address = ?, latitude = ?, longitude = ?, profile_photo = ?
               WHERE id = ?''',
            (phone, address, latitude, longitude, profile_photo, user_id)
        )
        db.commit()

        user = db.execute(
            '''SELECT id, name, email, phone, address, latitude, longitude, profile_photo, role
               FROM users WHERE id = ?''',
            (user_id,)
        ).fetchone()

        return jsonify(
            success=True,
            message='Profile updated successfully.',
            user={
                'id': user['id'], 'name': user['name'], 'email': user['email'],
                'phone': user['phone'] or '', 'address': user['address'] or '',
                'latitude': user['latitude'], 'longitude': user['longitude'],
                'profile_photo': user['profile_photo'] or '', 'role': user['role'] or 'user'
            }
        )
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        if db:
            db.close()
