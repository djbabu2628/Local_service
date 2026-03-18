"""
services/emergency_logic.py — Core Business Logic
Contains accept_job() and complete_job() with all validation.
"""

from datetime import datetime
from database.db import get_db


def accept_job(req_id: int, provider_id: int):
    """
    Assign a PENDING request to a provider.
    Returns: (response_dict, http_status_code)
    """
    try:
        db = get_db()

        # 1. Check provider exists and is AVAILABLE
        provider = db.execute(
            'SELECT id, availability, name FROM providers WHERE id = ?',
            (provider_id,)
        ).fetchone()

        if not provider:
            return {'success': False, 'message': 'Provider not found.'}, 404

        if provider['availability'] == 'BUSY':
            return {
                'success': False,
                'message': 'You already have an active job. Complete it before accepting a new one.'
            }, 409

        # 2. Check request exists and is still PENDING
        req = db.execute(
            'SELECT id, status FROM service_requests WHERE id = ?',
            (req_id,)
        ).fetchone()

        if not req:
            return {'success': False, 'message': 'Request not found.'}, 404

        if req['status'] != 'PENDING':
            return {
                'success': False,
                'message': 'This request has already been accepted by another provider.'
            }, 409

        # 3. Assign request → ASSIGNED + mark provider → BUSY
        db.execute(
            "UPDATE service_requests SET status = 'ASSIGNED', provider_id = ? WHERE id = ?",
            (provider_id, req_id)
        )
        db.execute(
            "UPDATE providers SET availability = 'BUSY' WHERE id = ?",
            (provider_id,)
        )
        db.commit()

        return {
            'success': True,
            'message': f'Job #{req_id} accepted! The customer will be notified.'
        }, 200

    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close()


def complete_job(req_id: int, provider_id: int):
    """
    Mark an ASSIGNED request as COMPLETED and free the provider.
    Returns: (response_dict, http_status_code)
    """
    try:
        db = get_db()

        # 1. Fetch request
        req = db.execute(
            'SELECT id, status, provider_id FROM service_requests WHERE id = ?',
            (req_id,)
        ).fetchone()

        if not req:
            return {'success': False, 'message': 'Request not found.'}, 404

        if req['status'] != 'ASSIGNED':
            return {'success': False, 'message': 'This job is not in ASSIGNED state.'}, 400

        if req['provider_id'] != provider_id:
            return {'success': False, 'message': 'Unauthorized: this job belongs to another provider.'}, 403

        # 2. Complete request + free provider
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            "UPDATE service_requests SET status = 'COMPLETED', completed_at = ? WHERE id = ?",
            (now, req_id)
        )
        db.execute(
            "UPDATE providers SET availability = 'AVAILABLE' WHERE id = ?",
            (provider_id,)
        )
        db.commit()

        return {
            'success': True,
            'message': 'Job completed successfully! You are now available for new requests. 🎉'
        }, 200

    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close()
