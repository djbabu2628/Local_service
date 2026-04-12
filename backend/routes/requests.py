import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from flask import Blueprint, jsonify, request

from database.db import DEFAULT_PLATFORM_FEE, DEFAULT_SERVICE_CHARGES, get_db
from services.emergency_logic import accept_job, complete_job

requests_bp = Blueprint('requests', __name__)


def parse_float(value):
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def map_url_from_booking(latitude, longitude, address):
    if latitude is not None and longitude is not None:
        return f'https://maps.google.com/maps?q={latitude},{longitude}&z=14&output=embed'
    if address:
        return f"https://maps.google.com/maps?q={urlparse.quote_plus(str(address))}&z=14&output=embed"
    return None


def booking_dict(row):
    booking = dict(row)
    booking['service_amount'] = float(booking.get('service_amount') or 0)
    booking['platform_fee'] = float(booking.get('platform_fee') or 0)
    booking['total_amount'] = float(booking.get('total_amount') or 0)
    booking['map_url'] = map_url_from_booking(
        booking.get('user_latitude'),
        booking.get('user_longitude'),
        booking.get('address'),
    )
    return booking


def payment_status_label(status):
    mapping = {'CREATED': 'Awaiting Payment', 'PAID': 'Paid', 'FAILED': 'Failed'}
    return mapping.get(status, status.title() if status else 'Unknown')


def create_razorpay_order(booking_id, total_amount):
    amount_paise = int(round(total_amount * 100))
    key_id = (os.getenv('RAZORPAY_KEY_ID') or '').strip()
    key_secret = (os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
    receipt = f'lses_booking_{booking_id}_{int(time.time())}'

    if key_id and key_secret:
        payload = json.dumps(
            {'amount': amount_paise, 'currency': 'INR', 'receipt': receipt, 'payment_capture': 1}
        ).encode()
        token = base64.b64encode(f'{key_id}:{key_secret}'.encode()).decode()
        req = urlrequest.Request(
            'https://api.razorpay.com/v1/orders',
            data=payload,
            headers={'Authorization': f'Basic {token}', 'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urlrequest.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return {
                    'gateway': 'RAZORPAY',
                    'order_id': data['id'],
                    'key_id': key_id,
                    'amount_paise': amount_paise,
                    'currency': 'INR',
                    'mock_mode': False,
                }
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError):
            pass

    return {
        'gateway': 'MOCK_RAZORPAY',
        'order_id': f'mock_order_{booking_id}_{int(time.time())}',
        'key_id': key_id or 'rzp_test_mock_key',
        'amount_paise': amount_paise,
        'currency': 'INR',
        'mock_mode': True,
    }


def upsert_payment(db, booking_id, provider_id, payment_data, service_amount, platform_fee, status='CREATED'):
    existing = db.execute('SELECT id FROM payments WHERE booking_id = ?', (booking_id,)).fetchone()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if existing:
        db.execute(
            """
            UPDATE payments
            SET provider_id = ?, gateway = ?, razorpay_order_id = ?, amount = ?, currency = ?,
                service_charge = ?, platform_fee = ?, status = ?, error_message = NULL, updated_at = ?
            WHERE booking_id = ?
            """,
            (
                provider_id,
                payment_data['gateway'],
                payment_data['order_id'],
                round(payment_data['amount_paise'] / 100, 2),
                payment_data['currency'],
                service_amount,
                platform_fee,
                status,
                now,
                booking_id,
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO payments (
                booking_id, provider_id, gateway, razorpay_order_id, amount, currency,
                service_charge, platform_fee, status, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                provider_id,
                payment_data['gateway'],
                payment_data['order_id'],
                round(payment_data['amount_paise'] / 100, 2),
                payment_data['currency'],
                service_amount,
                platform_fee,
                status,
                now,
            ),
        )


def fetch_provider(db, provider_id):
    return db.execute(
        """
        SELECT id, name, phone, service_type, base_charge, platform_fee
        FROM providers
        WHERE id = ?
        """,
        (provider_id,),
    ).fetchone()


def payment_payload_from_booking(booking_id, provider_name, description, payment_data):
    return {
        'booking_id': booking_id,
        'gateway': payment_data['gateway'],
        'key_id': payment_data['key_id'],
        'order_id': payment_data['order_id'],
        'amount': payment_data['amount_paise'],
        'currency': payment_data['currency'],
        'name': 'LSES Service Booking',
        'description': f'{provider_name} - {description[:60]}',
        'mock_mode': payment_data['mock_mode'],
    }


@requests_bp.route('/api/request', methods=['POST'])
def create_request():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    service_type = data.get('service_type', '').strip()
    description = data.get('description', '').strip()
    provider_id = data.get('provider_id')
    scheduled_date = data.get('scheduled_date', '').strip()
    scheduled_time = data.get('scheduled_time', '').strip()
    address = data.get('address', '').strip()
    user_latitude = parse_float(data.get('user_latitude'))
    user_longitude = parse_float(data.get('user_longitude'))
    payment_method = data.get('payment_method', 'ONLINE').strip().upper()

    if not all([user_id, name, phone, service_type, description, provider_id, scheduled_date, scheduled_time, address]):
        return jsonify(success=False, message='Please complete all booking fields.'), 400
    if not phone.isdigit() or len(phone) != 10:
        return jsonify(success=False, message='Phone number must be 10 digits.'), 400

    db = None
    try:
        db = get_db()
        provider = fetch_provider(db, provider_id)
        if not provider:
            return jsonify(success=False, message='Selected provider was not found.'), 404
        if provider['service_type'] != service_type:
            return jsonify(success=False, message='Selected provider does not match the chosen service type.'), 409

        active = db.execute(
            """
            SELECT id
            FROM service_requests
            WHERE user_id = ?
              AND status IN ('PENDING', 'ACCEPTED')
              AND payment_status IN ('CREATED', 'PAID')
            """,
            (user_id,),
        ).fetchone()
        if active:
            return jsonify(success=False, message='You already have an active booking. Complete or pay for it before creating another one.'), 409

        service_amount = float(provider['base_charge'] or DEFAULT_SERVICE_CHARGES.get(service_type, 399.0))
        platform_fee = float(provider['platform_fee'] or DEFAULT_PLATFORM_FEE)
        total_amount = round(service_amount + platform_fee, 2)

        # Cash payments are auto-marked as PAID
        initial_payment_status = 'PAID' if payment_method == 'CASH' else 'CREATED'

        cursor = db.execute(
            """
            INSERT INTO service_requests (
                user_id, customer_name, phone, service_type, description, status, provider_id,
                scheduled_date, scheduled_time, address, user_latitude, user_longitude,
                payment_status, service_amount, platform_fee, total_amount, payment_method
            )
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, name, phone, service_type, description, provider_id,
                scheduled_date, scheduled_time, address, user_latitude, user_longitude,
                initial_payment_status, service_amount, platform_fee, total_amount, payment_method,
            ),
        )
        booking_id = cursor.lastrowid

        if payment_method == 'CASH':
            # For cash, create a mock paid payment record
            mock_data = {
                'gateway': 'CASH',
                'order_id': f'cash_{booking_id}_{int(time.time())}',
                'key_id': '',
                'amount_paise': int(round(total_amount * 100)),
                'currency': 'INR',
                'mock_mode': True,
            }
            upsert_payment(db, booking_id, provider_id, mock_data, service_amount, platform_fee, status='PAID')
            db.commit()
            return jsonify(
                success=True,
                message='Booking created successfully! Pay cash to the provider on arrival.',
                request_id=booking_id,
                booking_id=booking_id,
                payment_method='CASH',
                summary={
                    'provider_name': provider['name'],
                    'service_charge': service_amount,
                    'platform_fee': platform_fee,
                    'total_amount': total_amount,
                },
            ), 201
        else:
            payment_data = create_razorpay_order(booking_id, total_amount)
            upsert_payment(db, booking_id, provider_id, payment_data, service_amount, platform_fee)
            db.commit()
            return jsonify(
                success=True,
                message='Booking created. Complete payment to notify the provider.',
                request_id=booking_id,
                booking_id=booking_id,
                payment_method='ONLINE',
                payment=payment_payload_from_booking(booking_id, provider['name'], description, payment_data),
                summary={
                    'provider_name': provider['name'],
                    'service_charge': service_amount,
                    'platform_fee': platform_fee,
                    'total_amount': total_amount,
                },
            ), 201
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@requests_bp.route('/api/payment/retry/<int:booking_id>', methods=['POST'])
def retry_payment(booking_id):
    db = None
    try:
        db = get_db()
        booking = db.execute(
            """
            SELECT sr.id, sr.provider_id, sr.description, sr.service_amount, sr.platform_fee, sr.total_amount,
                   sr.payment_status, sr.status, p.name AS provider_name
            FROM service_requests sr
            LEFT JOIN providers p ON sr.provider_id = p.id
            WHERE sr.id = ?
            """,
            (booking_id,),
        ).fetchone()
        if not booking:
            return jsonify(success=False, message='Booking not found.'), 404
        if booking['payment_status'] == 'PAID':
            return jsonify(success=False, message='This booking is already paid.'), 409
        if booking['status'] == 'COMPLETED':
            return jsonify(success=False, message='Completed bookings cannot be repaid.'), 409

        payment_data = create_razorpay_order(booking_id, float(booking['total_amount']))
        upsert_payment(db, booking_id, booking['provider_id'], payment_data, float(booking['service_amount']), float(booking['platform_fee']))
        db.execute("UPDATE service_requests SET payment_status = 'CREATED' WHERE id = ?", (booking_id,))
        db.commit()

        return jsonify(
            success=True,
            message='Payment session refreshed.',
            payment=payment_payload_from_booking(
                booking_id,
                booking['provider_name'] or 'Selected Provider',
                booking['description'] or 'Service booking',
                payment_data,
            ),
        )
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@requests_bp.route('/api/payment/verify', methods=['POST'])
def verify_payment():
    data = request.get_json(silent=True) or {}
    booking_id = data.get('booking_id')
    order_id = data.get('razorpay_order_id', '').strip()
    payment_id = data.get('razorpay_payment_id', '').strip()
    signature = data.get('razorpay_signature', '').strip()

    if not booking_id:
        return jsonify(success=False, message='booking_id is required.'), 400

    db = None
    try:
        db = get_db()
        payment = db.execute(
            "SELECT id, gateway, razorpay_order_id FROM payments WHERE booking_id = ?",
            (booking_id,),
        ).fetchone()
        if not payment:
            return jsonify(success=False, message='Payment record not found.'), 404

        key_secret = (os.getenv('RAZORPAY_KEY_SECRET') or '').strip()
        is_mock = payment['gateway'] == 'MOCK_RAZORPAY' or not key_secret
        if not is_mock:
            expected = hmac.new(
                key_secret.encode(),
                f'{order_id}|{payment_id}'.encode(),
                hashlib.sha256,
            ).hexdigest()
            if expected != signature or payment['razorpay_order_id'] != order_id:
                return jsonify(success=False, message='Payment verification failed.'), 400
        else:
            order_id = order_id or payment['razorpay_order_id']
            payment_id = payment_id or f'mock_payment_{booking_id}_{int(time.time())}'
            signature = signature or 'mock_signature'

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            """
            UPDATE payments
            SET razorpay_order_id = ?, razorpay_payment_id = ?, razorpay_signature = ?,
                status = 'PAID', updated_at = ?, error_message = NULL
            WHERE booking_id = ?
            """,
            (order_id, payment_id, signature, now, booking_id),
        )
        db.execute("UPDATE service_requests SET payment_status = 'PAID' WHERE id = ?", (booking_id,))
        db.commit()
        return jsonify(success=True, message='Payment verified successfully.')
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@requests_bp.route('/api/payment/fail', methods=['POST'])
def mark_payment_failed():
    data = request.get_json(silent=True) or {}
    booking_id = data.get('booking_id')
    message = data.get('message', 'Payment was not completed.').strip()
    if not booking_id:
        return jsonify(success=False, message='booking_id is required.'), 400

    db = None
    try:
        db = get_db()
        booking = db.execute('SELECT id FROM service_requests WHERE id = ?', (booking_id,)).fetchone()
        if not booking:
            return jsonify(success=False, message='Booking not found.'), 404

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            "UPDATE payments SET status = 'FAILED', error_message = ?, updated_at = ? WHERE booking_id = ?",
            (message, now, booking_id),
        )
        db.execute("UPDATE service_requests SET payment_status = 'FAILED' WHERE id = ?", (booking_id,))
        db.commit()
        return jsonify(success=True, message='Payment failure recorded.')
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@requests_bp.route('/api/requests', methods=['GET'])
def list_requests():
    service_type = request.args.get('service_type', '').strip()
    provider_id = request.args.get('provider_id', '').strip()

    db = None
    try:
        db = get_db()
        query = """
            SELECT sr.*, p.name AS provider_name, p.phone AS provider_phone
            FROM service_requests sr
            LEFT JOIN providers p ON sr.provider_id = p.id
            WHERE sr.status = 'PENDING' AND sr.payment_status = 'PAID'
        """
        params = []
        if provider_id:
            query += ' AND sr.provider_id = ?'
            params.append(provider_id)
        elif service_type:
            query += ' AND sr.service_type = ?'
            params.append(service_type)

        query += ' ORDER BY sr.scheduled_date ASC, sr.scheduled_time ASC, sr.created_at DESC'
        rows = db.execute(query, tuple(params)).fetchall()
        return jsonify(success=True, requests=[booking_dict(row) for row in rows])
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@requests_bp.route('/api/request/<int:req_id>/accept', methods=['POST'])
def accept(req_id):
    data = request.get_json(silent=True) or {}
    provider_id = data.get('provider_id')
    if not provider_id:
        return jsonify(success=False, message='provider_id is required.'), 400
    result, status = accept_job(req_id, provider_id)
    return jsonify(**result), status


@requests_bp.route('/api/request/<int:req_id>/complete', methods=['POST'])
def complete(req_id):
    data = request.get_json(silent=True) or {}
    provider_id = data.get('provider_id')
    if not provider_id:
        return jsonify(success=False, message='provider_id is required.'), 400
    result, status = complete_job(req_id, provider_id)
    return jsonify(**result), status


@requests_bp.route('/api/track', methods=['GET'])
def track():
    phone = request.args.get('phone', '').strip()
    if not phone:
        return jsonify(success=False, message='Phone number is required.'), 400

    db = None
    try:
        db = get_db()
        row = db.execute(
            """
            SELECT sr.*, p.name AS provider_name, p.phone AS provider_phone, pay.gateway
            FROM service_requests sr
            LEFT JOIN providers p ON sr.provider_id = p.id
            LEFT JOIN payments pay ON pay.booking_id = sr.id
            WHERE sr.phone = ?
            ORDER BY sr.created_at DESC
            LIMIT 1
            """,
            (phone,),
        ).fetchone()
        if not row:
            return jsonify(success=False, message='No booking found for this phone number. Please check and try again.'), 404

        booking = booking_dict(row)
        booking['payment_status_label'] = payment_status_label(booking.get('payment_status'))
        booking['payment_method'] = booking.get('payment_method') or 'ONLINE'
        return jsonify(success=True, request=booking)
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@requests_bp.route('/api/bookings/user/<int:user_id>', methods=['GET'])
def user_history(user_id):
    db = None
    try:
        db = get_db()
        rows = db.execute(
            """
            SELECT sr.*, p.name AS provider_name, p.phone AS provider_phone, pay.gateway
            FROM service_requests sr
            LEFT JOIN providers p ON sr.provider_id = p.id
            LEFT JOIN payments pay ON pay.booking_id = sr.id
            WHERE sr.user_id = ?
            ORDER BY sr.created_at DESC
            """,
            (user_id,),
        ).fetchall()
        bookings = []
        for row in rows:
            booking = booking_dict(row)
            booking['payment_status_label'] = payment_status_label(booking.get('payment_status'))
            bookings.append(booking)
        return jsonify(success=True, bookings=bookings)
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()


@requests_bp.route('/api/bookings/provider/<int:provider_id>', methods=['GET'])
def provider_history(provider_id):
    db = None
    try:
        db = get_db()
        rows = db.execute(
            """
            SELECT sr.*, u.name AS user_name, p.name AS provider_name, p.phone AS provider_phone, pay.gateway
            FROM service_requests sr
            LEFT JOIN users u ON sr.user_id = u.id
            LEFT JOIN providers p ON sr.provider_id = p.id
            LEFT JOIN payments pay ON pay.booking_id = sr.id
            WHERE sr.provider_id = ?
            ORDER BY sr.created_at DESC
            """,
            (provider_id,),
        ).fetchall()
        bookings = []
        for row in rows:
            booking = booking_dict(row)
            booking['payment_status_label'] = payment_status_label(booking.get('payment_status'))
            bookings.append(booking)
        return jsonify(success=True, bookings=bookings)
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500
    finally:
        if db:
            db.close()
