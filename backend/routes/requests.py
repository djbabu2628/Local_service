"""
routes/requests.py — Service Request Routes
POST /api/request             — Create emergency request
GET  /api/requests            — List pending requests (filtered by service_type)
POST /api/request/<id>/accept — Provider accepts a job
POST /api/request/<id>/complete — Provider completes a job
GET  /api/track               — Track by phone number
"""

from flask import Blueprint, request, jsonify
from database.db import get_db
from services.emergency_logic import accept_job, complete_job

requests_bp = Blueprint('requests', __name__)


def row_to_dict(row):
    """Convert sqlite3.Row to plain dict."""
    return dict(row) if row else None


# ── Create Request ────────────────────────────────────────────
@requests_bp.route('/api/request', methods=['POST'])
def create_request():
    data         = request.get_json(silent=True) or {}
    user_id      = data.get('user_id')
    name         = data.get('name', '').strip()
    phone        = data.get('phone', '').strip()
    service_type = data.get('service_type', '').strip()
    description  = data.get('description', '').strip()

    if not all([user_id, name, phone, service_type, description]):
        return jsonify(success=False, message='All fields are required.'), 400

    try:
        db = get_db()

        # Prevent duplicate active requests
        active = db.execute(
            "SELECT id FROM service_requests WHERE user_id = ? AND status IN ('PENDING','ASSIGNED')",
            (user_id,)
        ).fetchone()
        if active:
            return jsonify(
                success=False,
                message='You already have an active request. Please wait for it to be completed.'
            ), 409

        cursor = db.execute(
            """INSERT INTO service_requests
               (user_id, customer_name, phone, service_type, description, status)
               VALUES (?, ?, ?, ?, ?, 'PENDING')""",
            (user_id, name, phone, service_type, description)
        )
        db.commit()
        return jsonify(
            success=True,
            message='Emergency request submitted successfully!',
            request_id=cursor.lastrowid
        ), 201
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()


# ── List Pending Requests ─────────────────────────────────────
@requests_bp.route('/api/requests', methods=['GET'])
def list_requests():
    service_type = request.args.get('service_type', '').strip()

    try:
        db = get_db()
        if service_type:
            rows = db.execute(
                """SELECT sr.*, u.name AS user_name
                   FROM service_requests sr
                   LEFT JOIN users u ON sr.user_id = u.id
                   WHERE sr.status = 'PENDING' AND sr.service_type = ?
                   ORDER BY sr.created_at DESC""",
                (service_type,)
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT sr.*, u.name AS user_name
                   FROM service_requests sr
                   LEFT JOIN users u ON sr.user_id = u.id
                   WHERE sr.status = 'PENDING'
                   ORDER BY sr.created_at DESC"""
            ).fetchall()

        return jsonify(success=True, requests=[dict(r) for r in rows])
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()


# ── Accept Job ────────────────────────────────────────────────
@requests_bp.route('/api/request/<int:req_id>/accept', methods=['POST'])
def accept(req_id):
    data        = request.get_json(silent=True) or {}
    provider_id = data.get('provider_id')
    if not provider_id:
        return jsonify(success=False, message='provider_id is required.'), 400

    result, status = accept_job(req_id, provider_id)
    return jsonify(**result), status


# ── Complete Job ──────────────────────────────────────────────
@requests_bp.route('/api/request/<int:req_id>/complete', methods=['POST'])
def complete(req_id):
    data        = request.get_json(silent=True) or {}
    provider_id = data.get('provider_id')
    if not provider_id:
        return jsonify(success=False, message='provider_id is required.'), 400

    result, status = complete_job(req_id, provider_id)
    return jsonify(**result), status


# ── Track by Phone ────────────────────────────────────────────
@requests_bp.route('/api/track', methods=['GET'])
def track():
    phone = request.args.get('phone', '').strip()
    if not phone:
        return jsonify(success=False, message='Phone number is required.'), 400

    try:
        db = get_db()
        row = db.execute(
            """SELECT sr.*, p.name AS provider_name, p.phone AS provider_phone
               FROM service_requests sr
               LEFT JOIN providers p ON sr.provider_id = p.id
               WHERE sr.phone = ?
               ORDER BY sr.created_at DESC LIMIT 1""",
            (phone,)
        ).fetchone()

        if not row:
            return jsonify(
                success=False,
                message='No request found for this phone number. Check the number and try again.'
            ), 404

        return jsonify(success=True, request=dict(row))
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    finally:
        db.close()
