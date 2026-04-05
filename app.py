"""
═══════════════════════════════════════════════════════════════════════
  Secure AI-Powered Multilingual Telemedicine & Prescription System
  Main Application — Flask + SocketIO
═══════════════════════════════════════════════════════════════════════
"""

import os
import json
from functools import wraps
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

from config import Config
from database import init_db

# Services
from services.auth_service import register_user, login_user, verify_token, get_user_profile, update_patient_language, get_patient_by_user_id
from services.doctor_service import (
    list_doctors, get_doctor, get_doctor_by_user_id,
    set_availability, notify_doctor, get_pending_notifications, clear_notification
)
from services.consultation_service import (
    start_consultation, append_transcript, update_urgency,
    complete_consultation, get_consultation,
    get_active_consultation_for_doctor,
    get_patient_history, get_doctor_history
)
from services.ai_engine import (
    detect_urgency, analyze_symptoms, verify_medicine,
    suggest_prescription, suggest_diet, generate_disclaimer,
    translate_text, get_supported_languages
)
from services.prescription_service import (
    create_prescription, approve_prescription,
    get_prescription, get_prescription_by_id
)
<<<<<<< HEAD
from services.report_service import generate_report, get_report, get_patient_reports, get_patient_doctor_history
=======
from services.report_service import (
    generate_report, get_report, get_patient_reports, 
    approve_report, get_patient_approved_reports
)
>>>>>>> c90c73693dc229b32b181e7b680b9500e0c4c1c7

# ── App Setup ──────────────────────────────────────────────────
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize database
init_db()

# ── Auth Middleware ─────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication token required'}), 401
        result = verify_token(token)
        if not result['valid']:
            return jsonify({'error': result['error']}), 401
        request.user = result['payload']
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════
# PAGE ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/patient')
def patient_page():
    return render_template('patient_dashboard.html')

@app.route('/doctor')
def doctor_page():
    return render_template('doctor_dashboard.html')

@app.route('/report/<int:consultation_id>')
def report_page(consultation_id):
    return render_template('report.html', consultation_id=consultation_id)


# ═══════════════════════════════════════════════════════════════
# AUTH API
# ═══════════════════════════════════════════════════════════════

@app.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', '')

    if not all([name, email, password, role]):
        return jsonify({'error': 'All fields are required'}), 400

    extra = {}
    if role == 'doctor':
        extra['specialization'] = data.get('specialization', 'General Medicine')
        extra['experience_years'] = data.get('experience_years', 0)
    else:
        extra['age'] = data.get('age')
        extra['gender'] = data.get('gender')
        extra['blood_group'] = data.get('blood_group')

    result = register_user(name, email, password, role, **extra)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result), 201


@app.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not all([email, password]):
        return jsonify({'error': 'Email and password required'}), 400

    result = login_user(email, password)
    if 'error' in result:
        return jsonify(result), 401
    return jsonify(result)


@app.route('/auth/verify', methods=['GET'])
@token_required
def api_verify():
    profile = get_user_profile(request.user['user_id'])
    return jsonify({'valid': True, 'user': profile})


@app.route('/auth/update-language', methods=['POST'])
@token_required
def api_update_language():
    if request.user['role'] != 'patient':
        return jsonify({'error': 'Only patients can update language preferences'}), 403

    data = request.get_json()
    language = data.get('language', 'en')

    if language not in get_supported_languages():
        return jsonify({'error': 'Unsupported language'}), 400

    result = update_patient_language(request.user['user_id'], language)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
# DOCTOR API
# ═══════════════════════════════════════════════════════════════

@app.route('/doctors/list', methods=['GET'])
@token_required
def api_list_doctors():
    doctors = list_doctors()
    return jsonify({'doctors': doctors})


@app.route('/doctors/availability', methods=['POST'])
@token_required
def api_set_availability():
    data = request.get_json()
    doctor = get_doctor_by_user_id(request.user['user_id'])
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    result = set_availability(doctor['doctor_id'], data.get('available', True))
    # Broadcast availability change
    socketio.emit('doctor_availability_changed', {
        'doctor_id': doctor['doctor_id'],
        'available': data.get('available', True)
    }, room='lobby')
    return jsonify(result)


@app.route('/doctors/notify', methods=['POST'])
@token_required
def api_notify_doctor():
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    patient_id = data.get('patient_id')
    if not all([doctor_id, patient_id]):
        return jsonify({'error': 'doctor_id and patient_id required'}), 400
    result = notify_doctor(doctor_id, patient_id)
    if 'error' in result:
        return jsonify(result), 400
    # Send real-time notification to doctor
    socketio.emit('patient_request', {
        'doctor_id': doctor_id,
        'patient_id': patient_id,
        'message': result.get('message', '')
    }, room=f'doctor_{doctor_id}')
    return jsonify(result)


@app.route('/doctors/notifications', methods=['GET'])
@token_required
def api_get_notifications():
    doctor = get_doctor_by_user_id(request.user['user_id'])
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    result = get_pending_notifications(doctor['doctor_id'])
    return jsonify(result)


@app.route('/doctors/notifications/clear', methods=['POST'])
@token_required
def api_clear_notification():
    doctor = get_doctor_by_user_id(request.user['user_id'])
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    result = clear_notification(doctor['doctor_id'])
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
# CONSULTATION API
# ═══════════════════════════════════════════════════════════════

@app.route('/consult/start', methods=['POST'])
@token_required
def api_start_consultation():
    data = request.get_json()
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    if not all([patient_id, doctor_id]):
        return jsonify({'error': 'patient_id and doctor_id required'}), 400
    result = start_consultation(patient_id, doctor_id)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result), 201


@app.route('/consult/<int:consultation_id>', methods=['GET'])
@token_required
def api_get_consultation(consultation_id):
    result = get_consultation(consultation_id)
    if not result:
        return jsonify({'error': 'Consultation not found'}), 404
    return jsonify(result)


@app.route('/consult/active', methods=['GET'])
@token_required
def api_get_active_consultation():
    doctor = get_doctor_by_user_id(request.user['user_id'])
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    result = get_active_consultation_for_doctor(doctor['doctor_id'])
    return jsonify(result or {})


@app.route('/consult/<int:consultation_id>/complete', methods=['POST'])
@token_required
def api_complete_consultation(consultation_id):
    result = complete_consultation(consultation_id)
    socketio.emit('consultation_ended', {'consultation_id': consultation_id},
                  room=f'consultation_{consultation_id}')
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
# AI ANALYSIS API
# ═══════════════════════════════════════════════════════════════

@app.route('/analyse/urgency', methods=['POST'])
@token_required
def api_analyse_urgency():
    data = request.get_json()
    transcript = data.get('transcript', '')
    result = detect_urgency(transcript)
    return jsonify(result)


@app.route('/analyse/symptoms', methods=['POST'])
@token_required
def api_analyse_symptoms():
    data = request.get_json()
    transcript = data.get('transcript', '')
    result = analyze_symptoms(transcript)
    return jsonify(result)


@app.route('/analyse/translate', methods=['POST'])
@token_required
def api_translate():
    data = request.get_json()
    text = data.get('text', '')
    source_lang = data.get('source_lang', 'en')
    target_lang = data.get('target_lang', 'en')
    translated = translate_text(text, source_lang, target_lang)
    return jsonify({'original': text, 'translated': translated, 'source_lang': source_lang, 'target_lang': target_lang})


@app.route('/analyse/languages', methods=['GET'])
def api_get_languages():
    return jsonify(get_supported_languages())


# ═══════════════════════════════════════════════════════════════
# PRESCRIPTION API
# ═══════════════════════════════════════════════════════════════

@app.route('/prescription/verify', methods=['POST'])
@token_required
def api_verify_medicine():
    data = request.get_json()
    name = data.get('name', '')
    dosage = data.get('dosage', '')
    result = verify_medicine(name, dosage)
    return jsonify(result)


@app.route('/prescription/suggest', methods=['POST'])
@token_required
def api_suggest_prescription():
    data = request.get_json()
    diagnosis = data.get('diagnosis', '')
    result = suggest_prescription(diagnosis)
    return jsonify(result)


@app.route('/prescription/ai-suggest/<int:consultation_id>', methods=['GET'])
@token_required
def api_ai_suggest_from_transcript(consultation_id):
    """
    Read the full consultation transcript and return a complete AI-generated
    prescription draft: medicines, diet, exercise, symptoms, diagnosis, urgency.
    Doctor reviews and can edit before approving.
    """
    from services.consultation_service import get_consultation

    consultation = get_consultation(consultation_id)
    if not consultation:
        return jsonify({'error': 'Consultation not found'}), 404

    transcript = consultation.get('transcript', '')
    if not transcript:
        return jsonify({'error': 'No transcript available yet. Ask the patient to speak first.'}), 400

    # Full AI pipeline
    analysis   = analyze_symptoms(transcript)
    urgency    = detect_urgency(transcript)
    rx_suggest = suggest_prescription(analysis.get('diagnosis', ''))
    symptoms   = analysis.get('symptoms', [])
    diet_info  = suggest_diet(analysis.get('diagnosis', ''), symptoms=symptoms)

    return jsonify({
        'diagnosis':    analysis.get('diagnosis', ''),
        'cause':        analysis.get('cause', ''),
        'symptoms':     symptoms,
        'problem':      analysis.get('problem', ''),
        'precautions':  analysis.get('precautions', []),
        'tests':        analysis.get('tests', []),
        'confidence':   analysis.get('confidence', 0),
        'urgency':      urgency,
        'medicines':    rx_suggest.get('suggestions', []),
        'diet':         '\n'.join(diet_info.get('diet', [])),
        'exercise':     '\n'.join(diet_info.get('exercise', [])),
        'note':         rx_suggest.get('note', '')
    })


@app.route('/prescription/create', methods=['POST'])
@token_required
def api_create_prescription():
    data = request.get_json()
    consultation_id = data.get('consultation_id')
    medicines = data.get('medicines', [])
    diet = data.get('diet', '')
    exercise = data.get('exercise', '')
    notes = data.get('notes', '')
    if not consultation_id:
        return jsonify({'error': 'consultation_id required'}), 400
    result = create_prescription(consultation_id, medicines, diet, exercise, notes)
    return jsonify(result)


@app.route('/prescription/approve/<int:prescription_id>', methods=['POST'])
@token_required
def api_approve_prescription(prescription_id):
    result = approve_prescription(prescription_id)
    # Notify patient
    prescription = get_prescription_by_id(prescription_id)
    if prescription:
        socketio.emit('prescription_approved', {
            'prescription_id': prescription_id,
            'consultation_id': prescription['consultation_id']
        }, room=f'consultation_{prescription["consultation_id"]}')
    return jsonify(result)


@app.route('/prescription/<int:consultation_id>', methods=['GET'])
@token_required
def api_get_prescription(consultation_id):
    # Patients only see approved prescriptions; doctors see all
    require_approved = request.user.get('role') == 'patient'
    result = get_prescription(consultation_id, require_approved=require_approved)
    return jsonify(result or {})


# ═══════════════════════════════════════════════════════════════
# REPORT API
# ═══════════════════════════════════════════════════════════════

@app.route('/report/generate', methods=['POST'])
@token_required
def api_generate_report():
    data = request.get_json()
    consultation_id = data.get('consultation_id')
    patient_language = data.get('patient_language', 'en')  # native lang for patient report
    if not consultation_id:
        return jsonify({'error': 'consultation_id required'}), 400
    # If language not provided in payload, read original_language from the consultation
    if not patient_language or patient_language == 'en':
        from database import get_db, dict_from_row
        db = get_db()
        try:
            row = db.execute('SELECT original_language FROM consultations WHERE id = ?',
                             (consultation_id,)).fetchone()
            if row and row['original_language']:
                patient_language = row['original_language']
        finally:
            db.close()
    result = generate_report(consultation_id, patient_language=patient_language)
    return jsonify(result)


@app.route('/report/data/<int:consultation_id>', methods=['GET'])
@token_required
def api_get_report(consultation_id):
    result = get_report(consultation_id)
    return jsonify(result or {})


<<<<<<< HEAD
@app.route('/report/native/<int:consultation_id>', methods=['GET'])
@token_required
def api_get_native_report(consultation_id):
    """Return just the native-language report text for patient's dashboard."""
    result = get_report(consultation_id)
    if not result:
        return jsonify({'error': 'Report not found'}), 404
    return jsonify({
        'native_report': result.get('native_report', ''),
        'native_language': result.get('native_language', 'en'),
        'consultation_id': consultation_id
    })
=======
@app.route('/report/approve/<int:report_id>', methods=['POST'])
@token_required
def api_approve_report(report_id):
    result = approve_report(report_id)
    return jsonify(result)


@app.route('/patient/approved-reports', methods=['GET'])
@token_required
def api_get_approved_reports():
    if request.user.get('role') != 'patient':
        return jsonify({'error': 'Only patients can access this endpoint'}), 403
    patient = get_patient_by_user_id(request.user['user_id'])
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    reports = get_patient_approved_reports(patient['id'])
    return jsonify({'approved_reports': reports or []})
>>>>>>> c90c73693dc229b32b181e7b680b9500e0c4c1c7


# ═══════════════════════════════════════════════════════════════
# HISTORY API
# ═══════════════════════════════════════════════════════════════

@app.route('/history/patient/<int:patient_id>', methods=['GET'])
@token_required
def api_patient_history(patient_id):
    consultations = get_patient_history(patient_id)
    reports = get_patient_reports(patient_id)
    return jsonify({'consultations': consultations, 'reports': reports})


@app.route('/history/doctor', methods=['GET'])
@token_required
def api_doctor_history():
    doctor = get_doctor_by_user_id(request.user['user_id'])
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    consultations = get_doctor_history(doctor['doctor_id'])
    return jsonify({'consultations': consultations})


@app.route('/history/patient-doctor/<int:patient_id>/<int:doctor_id>', methods=['GET'])
@token_required
def api_patient_doctor_history(patient_id, doctor_id):
    """
    Returns all past completed consultations between a specific patient and doctor.
    Used by the doctor dashboard to display returning-patient history.
    """
    history = get_patient_doctor_history(patient_id, doctor_id)
    return jsonify({'history': history, 'is_returning': len(history) > 0, 'visit_count': len(history)})


# ═══════════════════════════════════════════════════════════════
# WEBSOCKET EVENTS (Real-time communication)
# ═══════════════════════════════════════════════════════════════

@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"❌ Client disconnected: {request.sid}")


@socketio.on('join_lobby')
def handle_join_lobby():
    join_room('lobby')
    emit('system_message', {'message': 'Connected to lobby'})


@socketio.on('join_doctor_room')
def handle_join_doctor_room(data):
    doctor_id = data.get('doctor_id')
    if doctor_id:
        join_room(f'doctor_{doctor_id}')
        emit('system_message', {'message': f'Joined doctor room {doctor_id}'})


@socketio.on('join_consultation')
def handle_join_consultation(data):
    consultation_id = data.get('consultation_id')
    if consultation_id:
        room = f'consultation_{consultation_id}'
        join_room(room)
        emit('system_message', {'message': f'Joined consultation {consultation_id}'}, room=request.sid)


@socketio.on('leave_consultation')
def handle_leave_consultation(data):
    consultation_id = data.get('consultation_id')
    if consultation_id:
        leave_room(f'consultation_{consultation_id}')


@socketio.on('send_message')
def handle_send_message(data):
    """
    Real-time consultation message routing with translation.

    Patient → server:  any language speech  → translate to English → save to DB + broadcast
    Doctor  → server:  English (or any lang) → save as-is + broadcast (patient translates client-side)
    """
    consultation_id = data.get('consultation_id')
    speaker         = data.get('speaker', 'unknown')
    text            = data.get('text', '').strip()
    original_text   = data.get('original_text', text)
    language        = data.get('language', 'en')
    timestamp       = data.get('timestamp', '')

    if not consultation_id or not text:
        return

    english_text = text

    # ── Patient speech: translate to English for DB + AI analysis ──
    if speaker == 'patient' and language != 'en':
        try:
            translated = translate_text(text, source_lang=language, target_lang='en')
            if translated and translated != text:
                english_text = translated
        except Exception as e:
            print(f'⚠️  Patient translation failed: {e}')
            english_text = text  # keep original on failure

    # Save the English version to DB (AI analysis works on English)
    append_transcript(consultation_id, speaker, english_text, 'en')

    # Run urgency detection on English text
    urgency = detect_urgency(english_text)
    if urgency['is_urgent']:
        update_urgency(consultation_id, urgency['severity'], urgency['keywords_found'])

    # ── Broadcast to the consultation room ──
    # Doctor sees: English translation of patient speech (or doctor's own words)
    # Patient sees: their own original speech echoed back, doctor's English (client translates)
    room = f'consultation_{consultation_id}'
    emit('new_message', {
        'speaker':      speaker,
        'text':         english_text,       # English version (shown to doctor, base for patient translation)
        'original_text': original_text,     # Original utterance (shown to patient as-spoken)
        'translated':   english_text != original_text,
        'language':     language,           # Source language key, e.g. 'hi'
        'timestamp':    timestamp,
        'urgency':      urgency
    }, room=room)

    # ── Forward urgency alert to the doctor's private room ──
    if urgency['is_urgent']:
        consultation = get_consultation(consultation_id)
        if consultation:
            emit('urgency_alert', {
                'consultation_id': consultation_id,
                'patient_name':    consultation.get('patient_name', 'Patient'),
                'severity':        urgency['severity'],
                'keywords':        urgency['keywords_found'],
                'message':         urgency['alert_message']
            }, room=f'doctor_{consultation["doctor_id"]}')


@socketio.on('typing')
def handle_typing(data):
    """Broadcast typing indicator."""
    consultation_id = data.get('consultation_id')
    speaker = data.get('speaker', '')
    emit('user_typing', {'speaker': speaker}, room=f'consultation_{consultation_id}', include_self=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    consultation_id = data.get('consultation_id')
    speaker = data.get('speaker', '')
    emit('user_stopped_typing', {'speaker': speaker}, room=f'consultation_{consultation_id}', include_self=False)


# ═══════════════════════════════════════════════════════════════
# INIT SERVICE FILE
# ═══════════════════════════════════════════════════════════════

# Create __init__.py for services package
services_init = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'services', '__init__.py')
if not os.path.exists(services_init):
    os.makedirs(os.path.dirname(services_init), exist_ok=True)
    with open(services_init, 'w') as f:
        f.write('# Services package\n')


# ═══════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 60)
    print("  🏥 Telemedicine System Starting...")
    print("  📍 URL: http://localhost:5000")
    print("  🔌 WebSocket: Enabled (eventlet)")
    print("═" * 60)
    socketio.run(app, host='0.0.0.0', port=5000, debug=Config.DEBUG)
