from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Doctor, Consultation, Notification, Message
from ai_engine import get_ai_response, generate_consultation_report, get_welcome_message

patient_bp = Blueprint('patient', __name__)


def require_patient(fn):
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity['role'] != 'patient':
            return jsonify({'error': 'Patient access required'}), 403
        return fn(*args, **kwargs)
    return wrapper


@patient_bp.route('/api/patient/doctors', methods=['GET'])
@jwt_required()
def get_doctors():
    """List all doctors with optional filter by specialization."""
    specialization = request.args.get('specialization', '')
    available_only = request.args.get('available', 'false').lower() == 'true'

    query = Doctor.query.join(User)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f'%{specialization}%'))
    if available_only:
        query = query.filter(Doctor.is_available == True)

    doctors = query.all()
    return jsonify([d.to_dict() for d in doctors]), 200


@patient_bp.route('/api/patient/doctors/specializations', methods=['GET'])
@jwt_required()
def get_specializations():
    specs = db.session.query(Doctor.specialization).distinct().all()
    return jsonify([s[0] for s in specs]), 200


@patient_bp.route('/api/patient/consult', methods=['POST'])
@require_patient
def request_consultation():
    """Patient requests a consultation with a specific doctor."""
    from app import socketio
    identity = get_jwt_identity()
    data = request.get_json()

    doctor_id = data.get('doctor_id')
    language  = data.get('language', 'en')

    if not doctor_id:
        return jsonify({'error': 'doctor_id is required'}), 400

    doctor_user = db.session.get(User, doctor_id)
    if not doctor_user or doctor_user.role != 'doctor':
        return jsonify({'error': 'Doctor not found'}), 404

    if not doctor_user.doctor_profile or not doctor_user.doctor_profile.is_available:
        return jsonify({'error': 'Doctor is not available'}), 400

    patient = db.session.get(User, identity['id'])

    # Create consultation record
    consult = Consultation(
        patient_id=identity['id'],
        doctor_id=doctor_id,
        language=language,
        status='pending'
    )
    db.session.add(consult)
    db.session.flush()

    # Add AI welcome message
    welcome = get_welcome_message(language)
    ai_msg = Message(
        consultation_id=consult.id,
        user_id=None,
        sender_role='ai',
        content=welcome,
        language=language
    )
    db.session.add(ai_msg)

    # Create notification for doctor
    notif_msg = f"New consultation request from {patient.name} (Age: {patient.age or 'N/A'}, Blood Group: {patient.blood_group or 'N/A'})"
    notif = Notification(
        doctor_id=doctor_id,
        patient_id=identity['id'],
        message=notif_msg,
        notif_type='consultation_request'
    )
    db.session.add(notif)
    db.session.commit()

    # Emit real-time notification to doctor's socket room
    socketio.emit('new_notification', notif.to_dict(), room=f"doctor_{doctor_id}")

    return jsonify({
        'message': 'Consultation requested successfully',
        'consultation': consult.to_dict(),
        'welcome_message': welcome
    }), 201


@patient_bp.route('/api/patient/consultations', methods=['GET'])
@require_patient
def get_consultations():
    identity = get_jwt_identity()
    consults = Consultation.query.filter_by(patient_id=identity['id'])\
                                 .order_by(Consultation.created_at.desc()).all()
    return jsonify([c.to_dict() for c in consults]), 200


@patient_bp.route('/api/patient/consultations/<int:consult_id>/chat', methods=['POST'])
@require_patient
def chat(consult_id):
    """Send a message to AI within a consultation."""
    identity = get_jwt_identity()
    consult = Consultation.query.filter_by(id=consult_id, patient_id=identity['id']).first()
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404

    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    # Save patient message
    patient_msg = Message(
        consultation_id=consult_id,
        user_id=identity['id'],
        sender_role='patient',
        content=user_message,
        language=consult.language
    )
    db.session.add(patient_msg)
    db.session.flush()

    # Build conversation history for Gemini (last 20 messages)
    past_msgs = consult.messages.order_by(Message.created_at).limit(20).all()
    history = []
    for m in past_msgs:
        role = 'user' if m.sender_role == 'patient' else 'model'
        history.append({'role': role, 'parts': [m.content]})

    # Get AI response
    result = get_ai_response(history[:-1], user_message)  # exclude last (just added)
    ai_reply = result['response']
    lang     = result['language']

    # Save AI message
    ai_msg = Message(
        consultation_id=consult_id,
        user_id=None,
        sender_role='ai',
        content=ai_reply,
        language=lang
    )
    db.session.add(ai_msg)

    # Update consultation language
    consult.language = lang
    db.session.commit()

    return jsonify({
        'patient_message': patient_msg.to_dict(),
        'ai_response':     ai_msg.to_dict()
    }), 200


@patient_bp.route('/api/patient/consultations/<int:consult_id>/report', methods=['POST'])
@require_patient
def generate_report(consult_id):
    """Generate AI text report for a consultation."""
    identity = get_jwt_identity()
    consult = Consultation.query.filter_by(id=consult_id, patient_id=identity['id']).first()
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404

    messages = [m.to_dict() for m in consult.messages.order_by(Message.created_at)]
    report   = generate_consultation_report(
        messages,
        consult.patient_user.name,
        consult.doctor_user.name
    )
    consult.report_text = report
    consult.status      = 'completed'
    db.session.commit()

    return jsonify({'report': report, 'consultation': consult.to_dict()}), 200


@patient_bp.route('/api/patient/consultations/<int:consult_id>/messages', methods=['GET'])
@require_patient
def get_messages(consult_id):
    identity = get_jwt_identity()
    consult = Consultation.query.filter_by(id=consult_id, patient_id=identity['id']).first()
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404
    msgs = [m.to_dict() for m in consult.messages.order_by(Message.created_at)]
    return jsonify(msgs), 200


@patient_bp.route('/api/patient/profile', methods=['GET'])
@require_patient
def get_profile():
    identity = get_jwt_identity()
    user = db.session.get(User, identity['id'])
    return jsonify(user.to_dict()), 200
