from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Doctor, Consultation, Notification

doctor_bp = Blueprint('doctor', __name__)


def require_doctor(fn):
    """Decorator to ensure the user is a doctor."""
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity['role'] != 'doctor':
            return jsonify({'error': 'Doctor access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


@doctor_bp.route('/api/doctor/profile', methods=['GET'])
@require_doctor
def get_profile():
    identity = get_jwt_identity()
    user = db.session.get(User, identity['id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    data = user.to_dict()
    if user.doctor_profile:
        data['doctor'] = user.doctor_profile.to_dict()
    return jsonify(data), 200


@doctor_bp.route('/api/doctor/availability', methods=['PUT'])
@require_doctor
def toggle_availability():
    identity = get_jwt_identity()
    user = db.session.get(User, identity['id'])
    if not user or not user.doctor_profile:
        return jsonify({'error': 'Doctor profile not found'}), 404

    data = request.get_json()
    user.doctor_profile.is_available = data.get('is_available', not user.doctor_profile.is_available)
    db.session.commit()

    return jsonify({
        'message': 'Availability updated',
        'is_available': user.doctor_profile.is_available
    }), 200


@doctor_bp.route('/api/doctor/notifications', methods=['GET'])
@require_doctor
def get_notifications():
    identity = get_jwt_identity()
    notifs = Notification.query.filter_by(doctor_id=identity['id'])\
                               .order_by(Notification.created_at.desc())\
                               .limit(50).all()
    return jsonify([n.to_dict() for n in notifs]), 200


@doctor_bp.route('/api/doctor/notifications/<int:notif_id>/read', methods=['PUT'])
@require_doctor
def mark_read(notif_id):
    identity = get_jwt_identity()
    notif = Notification.query.filter_by(id=notif_id, doctor_id=identity['id']).first()
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Marked as read'}), 200


@doctor_bp.route('/api/doctor/notifications/mark-all-read', methods=['PUT'])
@require_doctor
def mark_all_read():
    identity = get_jwt_identity()
    Notification.query.filter_by(doctor_id=identity['id'], is_read=False)\
                      .update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'}), 200


@doctor_bp.route('/api/doctor/consultations', methods=['GET'])
@require_doctor
def get_consultations():
    identity = get_jwt_identity()
    consults = Consultation.query.filter_by(doctor_id=identity['id'])\
                                 .order_by(Consultation.created_at.desc()).all()
    return jsonify([c.to_dict() for c in consults]), 200


@doctor_bp.route('/api/doctor/consultations/<int:consult_id>', methods=['GET'])
@require_doctor
def get_consultation(consult_id):
    identity = get_jwt_identity()
    consult = Consultation.query.filter_by(id=consult_id, doctor_id=identity['id']).first()
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404
    data = consult.to_dict()
    data['messages'] = [m.to_dict() for m in consult.messages.order_by('created_at')]
    return jsonify(data), 200


@doctor_bp.route('/api/doctor/consultations/<int:consult_id>/status', methods=['PUT'])
@require_doctor
def update_status(consult_id):
    identity = get_jwt_identity()
    consult = Consultation.query.filter_by(id=consult_id, doctor_id=identity['id']).first()
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404
    data = request.get_json()
    consult.status = data.get('status', consult.status)
    db.session.commit()
    return jsonify({'message': 'Status updated', 'status': consult.status}), 200


@doctor_bp.route('/api/doctor/stats', methods=['GET'])
@require_doctor
def get_stats():
    identity = get_jwt_identity()
    total      = Consultation.query.filter_by(doctor_id=identity['id']).count()
    completed  = Consultation.query.filter_by(doctor_id=identity['id'], status='completed').count()
    pending    = Consultation.query.filter_by(doctor_id=identity['id'], status='pending').count()
    unread     = Notification.query.filter_by(doctor_id=identity['id'], is_read=False).count()
    return jsonify({
        'total_consultations': total,
        'completed': completed,
        'pending': pending,
        'unread_notifications': unread
    }), 200
