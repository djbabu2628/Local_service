import hashlib
import math
from datetime import datetime
from urllib.parse import quote_plus

from flask import Blueprint, jsonify, request

from database.db import DEFAULT_PLATFORM_FEE, DEFAULT_SERVICE_CHARGES, get_db

providers_bp = Blueprint('providers', __name__)


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def parse_float(value):
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def haversine_distance(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None

    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_map_url(latitude, longitude, address):
    if latitude is not None and longitude is not None:
        return f'https://maps.google.com/maps?q={latitude},{longitude}&z=14&output=embed'
    if address:
        return f"https://maps.google.com/maps?q={quote_plus(str(address))}&z=14&output=embed"
    return None


def provider_payload(row, user_lat=None, user_lng=None):
    provider = dict(row)
    provider['base_charge'] = float(provider.get('base_charge') or 0)
    provider['platform_fee'] = float(provider.get('platform_fee') or DEFAULT_PLATFORM_FEE)
    provider['rating'] = round(float(provider.get('rating') or 0), 1)
    provider['total_charge'] = round(provider['base_charge'] + provider['platform_fee'], 2)
    provider['distance_km'] = haversine_distance(
        user_lat,
        user_lng,
        provider.get('latitude'),
        provider.get('longitude'),
    )
    provider['map_url'] = build_map_url(provider.get('latitude'), provider.get('longitude'), provider.get('address'))
    provider['profile_photo'] = provider.get('profile_photo') or ''
    provider['experience'] = provider.get('experience') or ''
    provider['charge_type'] = provider.get('charge_type') or 'per_visit'
    return provider


PROVIDER_SELECT_COLS = """id, name, email, phone, service_type, availability, address, latitude,
                   longitude, base_charge, platform_fee, rating, total_jobs,
                   profile_photo, experience, charge_type"""


@providers_bp.route('/api/provider/register', methods=['POST'])
def provider_register():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    service_type = data.get('service_type', '').strip()
    address = data.get('address', '').strip()
    latitude = parse_float(data.get('latitude'))
    longitude = parse_float(data.get('longitude'))
    base_charge = parse_float(data.get('base_charge'))
    rating = parse_float(data.get('rating')) or 4.5
    experience = data.get('experience', '').strip()
    charge_type = data.get('charge_type', 'per_visit').strip()
    profile_photo = data.get('profile_photo', '').strip()

    if not all([name, email, phone, password, service_type, address]):
        return jsonify(success=False, message='All fields are required.'), 400
    if len(password) < 6:
        return jsonify(success=False, message='Password must be at least 6 characters.'), 400
    if not phone.isdigit() or len(phone) != 10:
        return jsonify(success=False, message='Phone number must be 10 digits.'), 400

    charge = base_charge or DEFAULT_SERVICE_CHARGES.get(service_type, 399.0)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db = None
    try:
        db = get_db()
        existing = db.execute('SELECT id FROM providers WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify(success=False, message='This email is already registered.'), 409

        cursor = db.execute(
            """
            INSERT INTO providers (
                name, email, phone, password, service_type, availability, address,
                latitude, longitude, base_charge, platform_fee, rating, total_jobs,
                updated_at, experience, charge_type, profile_photo
            )
            VALUES (?, ?, ?, ?, ?, 'AVAILABLE', ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                name, email, phone, hash_pw(password), service_type, address,
                latitude, longitude, charge, DEFAULT_PLATFORM_FEE, rating,
                now, experience, charge_type, profile_photo,
            ),
        )
        db.commit()

        provider = db.execute(
            f'SELECT {PROVIDER_SELECT_COLS} FROM providers WHERE id = ?',
            (cursor.lastrowid,),
        ).fetchone()
        return jsonify(success=True, message='Provider account created successfully!', provider=provider_payload(provider)), 201
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@providers_bp.route('/api/provider/login', methods=['POST'])
def provider_login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not all([email, password]):
        return jsonify(success=False, message='Email and password are required.'), 400

    db = None
    try:
        db = get_db()
        row = db.execute(
            f'SELECT {PROVIDER_SELECT_COLS} FROM providers WHERE email = ? AND password = ?',
            (email, hash_pw(password)),
        ).fetchone()
        if not row:
            return jsonify(success=False, message='Invalid email or password.'), 401
        return jsonify(success=True, message='Login successful.', provider=provider_payload(row))
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@providers_bp.route('/api/providers', methods=['GET'])
def list_providers():
    service_type = request.args.get('service_type', '').strip()
    sort_by = request.args.get('sort', 'nearest').strip().lower()
    user_lat = parse_float(request.args.get('user_lat'))
    user_lng = parse_float(request.args.get('user_lng'))
    max_price = parse_float(request.args.get('max_price'))

    db = None
    try:
        db = get_db()
        query = f"""
            SELECT {PROVIDER_SELECT_COLS}
            FROM providers
            WHERE 1 = 1
        """
        params = []
        if service_type:
            query += ' AND service_type = ?'
            params.append(service_type)

        rows = db.execute(query, tuple(params)).fetchall()
        providers = [provider_payload(row, user_lat=user_lat, user_lng=user_lng) for row in rows]

        # Apply max_price filter after computing total_charge
        if max_price is not None:
            providers = [p for p in providers if p['total_charge'] <= max_price]

        if sort_by == 'price':
            providers.sort(key=lambda item: (item['total_charge'], -item['rating']))
        elif sort_by == 'rating':
            providers.sort(key=lambda item: (-item['rating'], item['total_charge']))
        else:
            providers.sort(
                key=lambda item: (
                    item['distance_km'] is None,
                    item['distance_km'] if item['distance_km'] is not None else float('inf'),
                    item['total_charge'],
                )
            )

        return jsonify(success=True, providers=providers)
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@providers_bp.route('/api/provider/<int:provider_id>/profile', methods=['GET'])
def get_provider_profile(provider_id):
    db = None
    try:
        db = get_db()
        row = db.execute(
            f'SELECT {PROVIDER_SELECT_COLS} FROM providers WHERE id = ?',
            (provider_id,),
        ).fetchone()
        if not row:
            return jsonify(success=False, message='Provider not found.'), 404
        return jsonify(success=True, provider=provider_payload(row))
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@providers_bp.route('/api/provider/<int:provider_id>/profile', methods=['PUT'])
def update_provider_profile(provider_id):
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    latitude = parse_float(data.get('latitude'))
    longitude = parse_float(data.get('longitude'))
    base_charge = parse_float(data.get('base_charge'))
    experience = data.get('experience', '').strip()
    charge_type = data.get('charge_type', 'per_visit').strip()
    profile_photo = data.get('profile_photo', '').strip()

    if not all([phone, address]) or base_charge is None:
        return jsonify(success=False, message='Phone, address, and service charge are required.'), 400
    if not phone.isdigit() or len(phone) != 10:
        return jsonify(success=False, message='Phone number must be 10 digits.'), 400

    db = None
    try:
        db = get_db()
        existing = db.execute('SELECT id FROM providers WHERE id = ?', (provider_id,)).fetchone()
        if not existing:
            return jsonify(success=False, message='Provider not found.'), 404

        db.execute(
            """
            UPDATE providers
            SET phone = ?, address = ?, latitude = ?, longitude = ?, base_charge = ?,
                experience = ?, charge_type = ?, profile_photo = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                phone, address, latitude, longitude, base_charge,
                experience, charge_type, profile_photo,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                provider_id,
            ),
        )
        db.commit()

        row = db.execute(
            f'SELECT {PROVIDER_SELECT_COLS} FROM providers WHERE id = ?',
            (provider_id,),
        ).fetchone()
        return jsonify(success=True, message='Profile updated successfully.', provider=provider_payload(row))
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@providers_bp.route('/api/provider/stats/<int:provider_id>', methods=['GET'])
def provider_stats(provider_id):
    db = None
    try:
        db = get_db()
        provider = db.execute(
            f'SELECT {PROVIDER_SELECT_COLS} FROM providers WHERE id = ?',
            (provider_id,),
        ).fetchone()
        if not provider:
            return jsonify(success=False, message='Provider not found.'), 404

        completed = db.execute(
            "SELECT COUNT(*) AS cnt FROM service_requests WHERE provider_id = ? AND status = 'COMPLETED'",
            (provider_id,),
        ).fetchone()['cnt']
        active_count = db.execute(
            "SELECT COUNT(*) AS cnt FROM service_requests WHERE provider_id = ? AND status = 'ACCEPTED'",
            (provider_id,),
        ).fetchone()['cnt']
        pending_count = db.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM service_requests
            WHERE status = 'PENDING' AND payment_status = 'PAID' AND provider_id = ?
            """,
            (provider_id,),
        ).fetchone()['cnt']

        active_job = db.execute(
            """
            SELECT sr.id, sr.customer_name, sr.phone, sr.service_type, sr.description, sr.created_at,
                   sr.scheduled_date, sr.scheduled_time, sr.address, sr.user_latitude, sr.user_longitude,
                   sr.payment_status, sr.total_amount
            FROM service_requests sr
            WHERE sr.provider_id = ? AND sr.status = 'ACCEPTED'
            ORDER BY sr.accepted_at DESC, sr.created_at DESC
            LIMIT 1
            """,
            (provider_id,),
        ).fetchone()

        active_job_dict = dict(active_job) if active_job else None
        if active_job_dict:
            active_job_dict['map_url'] = build_map_url(
                active_job_dict.get('user_latitude'),
                active_job_dict.get('user_longitude'),
                active_job_dict.get('address'),
            )

        return jsonify(
            success=True,
            stats={
                'completed_jobs': completed,
                'active_jobs': active_count,
                'pending_jobs': pending_count,
                'active_job': active_job_dict,
                'provider': provider_payload(provider),
            },
        )
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()
