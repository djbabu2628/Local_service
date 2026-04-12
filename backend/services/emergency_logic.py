from datetime import datetime

from database.db import get_db


def accept_job(req_id: int, provider_id: int):
    db = None
    try:
        db = get_db()

        provider = db.execute(
            """
            SELECT id, availability, service_type
            FROM providers
            WHERE id = ?
            """,
            (provider_id,),
        ).fetchone()
        if not provider:
            return {'success': False, 'message': 'Provider not found.'}, 404

        if provider['availability'] == 'BUSY':
            return {
                'success': False,
                'message': 'You already have an active booking. Complete it before accepting another one.',
            }, 409

        booking = db.execute(
            """
            SELECT id, status, provider_id, service_type, payment_status
            FROM service_requests
            WHERE id = ?
            """,
            (req_id,),
        ).fetchone()
        if not booking:
            return {'success': False, 'message': 'Booking not found.'}, 404

        if booking['status'] != 'PENDING':
            return {'success': False, 'message': 'This booking is no longer pending.'}, 409

        if booking['payment_status'] != 'PAID':
            return {'success': False, 'message': 'Payment is still pending for this booking.'}, 409

        if booking['service_type'] != provider['service_type']:
            return {'success': False, 'message': 'This booking belongs to a different service category.'}, 409

        if booking['provider_id'] and booking['provider_id'] != provider_id:
            return {'success': False, 'message': 'This booking was requested from another provider.'}, 403

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            """
            UPDATE service_requests
            SET status = 'ACCEPTED', provider_id = ?, accepted_at = ?
            WHERE id = ?
            """,
            (provider_id, now, req_id),
        )
        db.execute(
            "UPDATE providers SET availability = 'BUSY', updated_at = ? WHERE id = ?",
            (now, provider_id),
        )
        db.commit()

        return {'success': True, 'message': f'Booking #{req_id} accepted successfully.'}, 200
    except Exception as exc:
        return {'success': False, 'message': str(exc)}, 500
    finally:
        if db:
            db.close()


def complete_job(req_id: int, provider_id: int):
    db = None
    try:
        db = get_db()
        booking = db.execute(
            'SELECT id, status, provider_id FROM service_requests WHERE id = ?',
            (req_id,),
        ).fetchone()
        if not booking:
            return {'success': False, 'message': 'Booking not found.'}, 404

        if booking['status'] != 'ACCEPTED':
            return {'success': False, 'message': 'This booking is not in ACCEPTED state.'}, 400

        if booking['provider_id'] != provider_id:
            return {'success': False, 'message': 'Unauthorized: this booking belongs to another provider.'}, 403

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            "UPDATE service_requests SET status = 'COMPLETED', completed_at = ? WHERE id = ?",
            (now, req_id),
        )
        db.execute(
            """
            UPDATE providers
            SET availability = 'AVAILABLE',
                total_jobs = COALESCE(total_jobs, 0) + 1,
                updated_at = ?
            WHERE id = ?
            """,
            (now, provider_id),
        )
        db.commit()

        return {
            'success': True,
            'message': 'Booking completed successfully. You are available for new requests now.',
        }, 200
    except Exception as exc:
        return {'success': False, 'message': str(exc)}, 500
    finally:
        if db:
            db.close()
