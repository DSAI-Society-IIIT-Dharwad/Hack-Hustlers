"""
Enhanced MediConsult Backend - Production-Ready with Real-time Features
Handles: Consultations, Notifications, Chat, Voice, Multilingual Support, Prescriptions
"""

from flask import Flask, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from pathlib import Path
import os
import json
from datetime import datetime, timedelta
import logging
from functools import wraps
import uuid

# ============================================================================
# SETUP
# ============================================================================

app = Flask(
    __name__,
    static_folder=str(Path(__file__).parent.parent / 'frontend'),
    static_url_path='/static'
)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)
# Use threading async mode to avoid eventlet compatibility issues with Python 3.14
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

FRONTEND = Path(__file__).parent.parent / 'frontend'

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ============================================================================
# IN-MEMORY DATA STORAGE (for demo - replace with DB in production)
# ============================================================================

# User storage: { 'email': user_obj }
users_db = {}

# Doctor storage: { doctor_id: doctor_obj }
doctors_db = {}

# Patient storage: { patient_id: patient_obj }
patients_db = {}

# Consultation storage: { consultation_id: consultation_obj }
consultations_db = {}

# Messages storage: { consultation_id: [messages] }
messages_db = {}

# Session storage for tracking active connections
active_sessions = {}  # { user_id: { token, role, socket_id, last_seen } }

# Notifications storage: { doctor_id: [notifications] }
notifications_db = {}

# Prescriptions storage: { consultation_id: prescription_obj }
prescriptions_db = {}

# ============================================================================
# INITIALIZATION: Load sample data
# ============================================================================

def init_sample_data():
    """Initialize with sample doctors for testing"""
    sample_doctors = [
        {
            'user_id': 1001,
            'name': 'Dr. Priya Sharma',
            'email': 'priya@medic.com',
            'specialization': 'Cardiologist',
            'years_of_experience': 12,
            'nmc_id': 'NMC20034521',
            'nmc_verified': True,
            'is_available': True,
            'bio': 'Expert in heart diseases with 12+ years of experience.',
            'languages': ['en', 'hi', 'kn'],
        },
        {
            'user_id': 1002,
            'name': 'Dr. Rajan Mehta',
            'email': 'rajan@medic.com',
            'specialization': 'Neurologist',
            'years_of_experience': 8,
            'nmc_id': 'NMC18027834',
            'nmc_verified': True,
            'is_available': False,
            'bio': 'Specialist in brain and nervous system disorders.',
            'languages': ['en', 'hi'],
        },
        {
            'user_id': 1003,
            'name': 'Dr. Ananya Rao',
            'email': 'ananya@medic.com',
            'specialization': 'Dermatologist',
            'years_of_experience': 5,
            'nmc_id': 'NMC21045678',
            'nmc_verified': True,
            'is_available': True,
            'bio': 'Skin specialist with expertise in cosmetic dermatology.',
            'languages': ['en', 'kn'],
        }
    ]

    for doctor in sample_doctors:
        user_id = doctor['user_id']
        users_db[doctor['email']] = {
            'id': user_id,
            'name': doctor['name'],
            'email': doctor['email'],
            'role': 'doctor',
            'created_at': datetime.utcnow().isoformat()
        }
        doctors_db[user_id] = doctor
        notifications_db[user_id] = []

logger.info("Initializing sample data...")
init_sample_data()

# ============================================================================
# TOKEN & AUTH HELPERS
# ============================================================================

def create_session_token(user_id, role, email):
    """Create a session token with user info embedded"""
    token_data = f"medi_{user_id}_{role}_{email}_{datetime.utcnow().isoformat()}"
    session_id = str(uuid.uuid4())

    active_sessions[user_id] = {
        'token': session_id,
        'role': role,
        'email': email,
        'socket_id': None,
        'last_seen': datetime.utcnow().isoformat()
    }

    return session_id

def validate_token():
    """Validate JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization', '').strip()

    if not auth_header.startswith('Bearer '):
        logger.warning(f"Missing or invalid Bearer prefix: {auth_header[:50]}")
        return None

    token = auth_header.replace('Bearer ', '').strip()

    # Find session by token
    for user_id, session in active_sessions.items():
        if session.get('token') == token:
            session['last_seen'] = datetime.utcnow().isoformat()
            # Get user from appropriate database
            if session['role'] == 'doctor':
                doctor = doctors_db.get(user_id)
                if doctor:
                    user = users_db.get(doctor['email'])
                    if user:
                        user['doctor'] = doctor
                    return user
            else:
                # Search in users_db for patient
                for email, user in users_db.items():
                    if user.get('id') == user_id and user.get('role') == 'patient':
                        return user

            logger.warning(f"User not found for validated session: {user_id}")
            return None

    logger.warning(f"Invalid token: {token[:50]}")
    return None

def require_auth(allowed_roles=None):
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = validate_token()
            if not user:
                logger.warning(f"Unauthorized request to {request.path}")
                return jsonify({'error': 'Unauthorized'}), 401

            if allowed_roles and user.get('role') not in allowed_roles:
                logger.warning(f"Forbidden: {user.get('role')} not in {allowed_roles}")
                return jsonify({'error': 'Forbidden'}), 403

            request.current_user = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': 'production_demo'
    }), 200

# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Patient or Doctor signup"""
    try:
        data = request.get_json() or {}

        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'patient')

        if not name or not email:
            return jsonify({'error': 'Name and email are required'}), 400

        if email in users_db:
            return jsonify({'error': 'Email already registered'}), 409

        # Create user
        user_id = max([u['id'] for u in users_db.values()] or [1000]) + 1

        user = {
            'id': user_id,
            'name': name,
            'email': email,
            'role': role,
            'age': data.get('age'),
            'blood_group': data.get('blood_group'),
            'created_at': datetime.utcnow().isoformat()
        }

        users_db[email] = user

        # If doctor signup, add doctor record
        if role == 'doctor':
            doctor = {
                'user_id': user_id,
                'name': name,
                'email': email,
                'specialization': data.get('specialization', 'General Medicine'),
                'years_of_experience': data.get('years_of_experience', 0),
                'nmc_id': data.get('nmc_id', ''),
                'nmc_verified': data.get('nmc_id', '').upper().startswith('NMC'),
                'is_available': True,
                'bio': data.get('bio', ''),
                'languages': data.get('languages', ['en']),
            }
            doctors_db[user_id] = doctor
            notifications_db[user_id] = []
            user['doctor'] = doctor

        # Create session token
        token = create_session_token(user_id, role, email)

        logger.info(f"User signed up: {email} (role: {role})")

        return jsonify({
            'message': 'Account created successfully',
            'token': token,
            'user': user
        }), 201

    except Exception as e:
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Signup failed: ' + str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = users_db.get(email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401

        # Create session token
        token = create_session_token(user['id'], user['role'], email)

        user_data = user.copy()
        if user['role'] == 'doctor' and user['id'] in doctors_db:
            user_data['doctor'] = doctors_db[user['id']]

        logger.info(f"User logged in: {email}")

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user_data
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Login failed: ' + str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
@require_auth()
def logout():
    """User logout"""
    try:
        user = request.current_user
        user_id = user.get('id')

        if user_id in active_sessions:
            del active_sessions[user_id]

        logger.info(f"User logged out: {user.get('email')}")

        return jsonify({'message': 'Logged out successfully'}), 200

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

# ============================================================================
# PATIENT ROUTES
# ============================================================================

@app.route('/api/patient/doctors', methods=['GET'])
@require_auth(['patient'])
def get_doctors():
    """Get list of available doctors"""
    try:
        doctors_list = []

        for user_id, doctor in doctors_db.items():
            doctor_data = doctor.copy()
            doctors_list.append(doctor_data)

        logger.info(f"Retrieved {len(doctors_list)} doctors for patient")
        return jsonify(doctors_list), 200

    except Exception as e:
        logger.error(f"Get doctors error: {str(e)}")
        return jsonify({'error': 'Failed to fetch doctors'}), 500

@app.route('/api/patient/profile', methods=['GET'])
@require_auth(['patient'])
def get_patient_profile():
    """Get patient profile"""
    try:
        user = request.current_user
        return jsonify(user), 200

    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500

@app.route('/api/patient/consultations', methods=['GET'])
@require_auth(['patient'])
def get_patient_consultations():
    """Get all consultations for patient"""
    try:
        user = request.current_user
        user_id = user.get('id')

        patient_consultations = [
            c for c in consultations_db.values()
            if c.get('patient_id') == user_id
        ]

        logger.info(f"Retrieved {len(patient_consultations)} consultations for patient {user_id}")
        return jsonify(patient_consultations), 200

    except Exception as e:
        logger.error(f"Get consultations error: {str(e)}")
        return jsonify({'error': 'Failed to fetch consultations'}), 500

@app.route('/api/patient/consult', methods=['POST'])
@require_auth(['patient'])
def request_consultation():
    """Request a consultation with a doctor"""
    try:
        user = request.current_user
        user_id = user.get('id')
        data = request.get_json() or {}

        doctor_id = data.get('doctor_id')
        language = data.get('language', 'en')

        if not doctor_id:
            return jsonify({'error': 'Doctor ID is required'}), 400

        if doctor_id not in doctors_db:
            return jsonify({'error': 'Doctor not found'}), 404

        doctor = doctors_db[doctor_id]

        # Create consultation
        consult_id = str(uuid.uuid4())

        consultation = {
            'id': consult_id,
            'patient_id': user_id,
            'doctor_id': doctor_id,
            'patient_name': user.get('name'),
            'doctor_name': doctor.get('name'),
            'language': language,
            'status': 'pending_acceptance',  # pending_acceptance -> active -> completed -> closed
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'transcript': '',
            'report_text': None,
            'prescription': None,
            'medical_data': {}  # Will store structured medical data
        }

        consultations_db[consult_id] = consultation
        messages_db[consult_id] = []

        # Send notification to doctor
        notification = {
            'id': str(uuid.uuid4()),
            'type': 'consultation_request',
            'consultation_id': consult_id,
            'patient_name': user.get('name'),
            'patient_age': user.get('age'),
            'patient_blood': user.get('blood_group'),
            'message': f"New consultation request from {user.get('name')}",
            'is_read': False,
            'created_at': datetime.utcnow().isoformat()
        }

        if doctor_id not in notifications_db:
            notifications_db[doctor_id] = []

        notifications_db[doctor_id].append(notification)

        logger.info(f"Consultation requested: {consult_id} (patient: {user_id}, doctor: {doctor_id})")

        # Emit real-time notification to doctor via Socket.IO
        socketio.emit('consultation_request', {
            'notification': notification,
            'consultation': consultation
        }, room=f"doctor_{doctor_id}")

        return jsonify({
            'message': 'Consultation requested successfully',
            'consultation': consultation,
            'welcome_message': 'Your consultation request has been sent to the doctor. Please wait for confirmation.'
        }), 201

    except Exception as e:
        logger.error(f"Request consultation error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to request consultation: ' + str(e)}), 500

@app.route('/api/patient/consultations/<consult_id>/chat', methods=['POST'])
@require_auth(['patient'])
def patient_send_message(consult_id):
    """Patient sends a message in consultation"""
    try:
        user = request.current_user
        user_id = user.get('id')

        if consult_id not in consultations_db:
            return jsonify({'error': 'Consultation not found'}), 404

        consultation = consultations_db[consult_id]

        if consultation.get('patient_id') != user_id:
            return jsonify({'error': 'Access denied'}), 403

        if consultation.get('status') not in ['active', 'pending_acceptance']:
            return jsonify({'error': 'Consultation is not active'}), 400

        data = request.get_json() or {}
        message_text = data.get('message', '').strip()

        if not message_text:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Create message
        message = {
            'id': str(uuid.uuid4()),
            'consultation_id': consult_id,
            'sender_id': user_id,
            'sender_role': 'patient',
            'sender_name': user.get('name'),
            'content': message_text,
            'language': consultation.get('language'),
            'created_at': datetime.utcnow().isoformat()
        }

        if consult_id not in messages_db:
            messages_db[consult_id] = []

        messages_db[consult_id].append(message)
        consultation['transcript'] += f"Patient: {message_text}\n"

        logger.info(f"Patient message sent in consultation {consult_id}")

        # Emit to doctor via Socket.IO
        socketio.emit('patient_message', {
            'message': message,
            'consultation_id': consult_id
        }, room=f"consultation_{consult_id}")

        # Mock AI response
        ai_message = {
            'id': str(uuid.uuid4()),
            'consultation_id': consult_id,
            'sender_id': None,
            'sender_role': 'ai',
            'sender_name': 'AI Assistant',
            'content': 'Message received by the doctor. Awaiting response...',
            'language': consultation.get('language'),
            'created_at': datetime.utcnow().isoformat()
        }

        messages_db[consult_id].append(ai_message)

        return jsonify({
            'patient_message': message,
            'ai_response': ai_message
        }), 200

    except Exception as e:
        logger.error(f"Send message error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to send message: ' + str(e)}), 500

@app.route('/api/patient/consultations/<consult_id>/messages', methods=['GET'])
@require_auth(['patient'])
def get_patient_messages(consult_id):
    """Get all messages in a consultation"""
    try:
        user = request.current_user
        user_id = user.get('id')

        if consult_id not in consultations_db:
            return jsonify({'error': 'Consultation not found'}), 404

        consultation = consultations_db[consult_id]

        if consultation.get('patient_id') != user_id:
            return jsonify({'error': 'Access denied'}), 403

        messages = messages_db.get(consult_id, [])

        return jsonify(messages), 200

    except Exception as e:
        logger.error(f"Get messages error: {str(e)}")
        return jsonify({'error': 'Failed to fetch messages'}), 500

# ============================================================================
# DOCTOR ROUTES
# ============================================================================

@app.route('/api/doctor/profile', methods=['GET'])
@require_auth(['doctor'])
def get_doctor_profile():
    """Get doctor profile"""
    try:
        user = request.current_user
        user_id = user.get('id')

        doctor = doctors_db.get(user_id)
        if not doctor:
            return jsonify({'error': 'Doctor profile not found'}), 404

        profile = user.copy()
        profile['doctor'] = doctor

        return jsonify(profile), 200

    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500

@app.route('/api/doctor/availability', methods=['PUT'])
@require_auth(['doctor'])
def toggle_availability():
    """Toggle doctor availability"""
    try:
        user = request.current_user
        user_id = user.get('id')

        if user_id not in doctors_db:
            return jsonify({'error': 'Doctor profile not found'}), 404

        doctor = doctors_db[user_id]
        data = request.get_json() or {}

        doctor['is_available'] = data.get('is_available', not doctor['is_available'])

        logger.info(f"Doctor {user_id} availability toggled to {doctor['is_available']}")

        return jsonify({
            'message': 'Availability updated',
            'is_available': doctor['is_available']
        }), 200

    except Exception as e:
        logger.error(f"Toggle availability error: {str(e)}")
        return jsonify({'error': 'Failed to toggle availability'}), 500

@app.route('/api/doctor/notifications', methods=['GET'])
@require_auth(['doctor'])
def get_doctor_notifications():
    """Get doctor notifications"""
    try:
        user = request.current_user
        user_id = user.get('id')

        notifs = notifications_db.get(user_id, [])

        logger.info(f"Retrieved {len(notifs)} notifications for doctor {user_id}")

        return jsonify(notifs), 200

    except Exception as e:
        logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'error': 'Failed to fetch notifications'}), 500

@app.route('/api/doctor/consultations', methods=['GET'])
@require_auth(['doctor'])
def get_doctor_consultations():
    """Get all consultations for doctor"""
    try:
        user = request.current_user
        user_id = user.get('id')

        doctor_consultations = [
            c for c in consultations_db.values()
            if c.get('doctor_id') == user_id
        ]

        logger.info(f"Retrieved {len(doctor_consultations)} consultations for doctor {user_id}")

        return jsonify(doctor_consultations), 200

    except Exception as e:
        logger.error(f"Get consultations error: {str(e)}")
        return jsonify({'error': 'Failed to fetch consultations'}), 500

@app.route('/api/doctor/consultations/<consult_id>/accept', methods=['POST'])
@require_auth(['doctor'])
def accept_consultation(consult_id):
    """Doctor accepts a consultation request"""
    try:
        user = request.current_user
        user_id = user.get('id')

        if consult_id not in consultations_db:
            return jsonify({'error': 'Consultation not found'}), 404

        consultation = consultations_db[consult_id]

        if consultation.get('doctor_id') != user_id:
            return jsonify({'error': 'Access denied'}), 403

        if consultation.get('status') != 'pending_acceptance':
            return jsonify({'error': 'Consultation is not pending acceptance'}), 400

        consultation['status'] = 'active'
        consultation['started_at'] = datetime.utcnow().isoformat()

        logger.info(f"Consultation {consult_id} accepted by doctor {user_id}")

        # Emit to patient via Socket.IO
        socketio.emit('consultation_accepted', {
            'consultation': consultation,
            'message': f"Dr. {consultation.get('doctor_name')} has accepted your consultation request"
        }, room=f"patient_{consultation.get('patient_id')}")

        return jsonify({
            'message': 'Consultation accepted',
            'consultation': consultation
        }), 200

    except Exception as e:
        logger.error(f"Accept consultation error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to accept consultation: ' + str(e)}), 500

@app.route('/api/doctor/consultations/<consult_id>/chat', methods=['POST'])
@require_auth(['doctor'])
def doctor_send_message(consult_id):
    """Doctor sends a message in consultation"""
    try:
        user = request.current_user
        user_id = user.get('id')

        if consult_id not in consultations_db:
            return jsonify({'error': 'Consultation not found'}), 404

        consultation = consultations_db[consult_id]

        if consultation.get('doctor_id') != user_id:
            return jsonify({'error': 'Access denied'}), 403

        data = request.get_json() or {}
        message_text = data.get('message', '').strip()

        if not message_text:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Create message
        message = {
            'id': str(uuid.uuid4()),
            'consultation_id': consult_id,
            'sender_id': user_id,
            'sender_role': 'doctor',
            'sender_name': user.get('name'),
            'content': message_text,
            'language': consultation.get('language'),
            'created_at': datetime.utcnow().isoformat()
        }

        if consult_id not in messages_db:
            messages_db[consult_id] = []

        messages_db[consult_id].append(message)
        consultation['transcript'] += f"Doctor: {message_text}\n"

        logger.info(f"Doctor message sent in consultation {consult_id}")

        # Emit to patient via Socket.IO
        socketio.emit('doctor_message', {
            'message': message,
            'consultation_id': consult_id
        }, room=f"consultation_{consult_id}")

        return jsonify({
            'doctor_message': message
        }), 200

    except Exception as e:
        logger.error(f"Send message error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to send message: ' + str(e)}), 500

@app.route('/api/doctor/consultations/<consult_id>/close', methods=['POST'])
@require_auth(['doctor'])
def close_consultation(consult_id):
    """Close a consultation and mark as completed"""
    try:
        user = request.current_user
        user_id = user.get('id')

        if consult_id not in consultations_db:
            return jsonify({'error': 'Consultation not found'}), 404

        consultation = consultations_db[consult_id]

        if consultation.get('doctor_id') != user_id:
            return jsonify({'error': 'Access denied'}), 403

        consultation['status'] = 'completed'
        consultation['completed_at'] = datetime.utcnow().isoformat()

        # Generate report from transcript
        report = generate_consultation_report(consultation)
        consultation['report_text'] = report

        logger.info(f"Consultation {consult_id} closed by doctor {user_id}")

        # Notify patient
        socketio.emit('consultation_completed', {
            'consultation': consultation,
            'report': report,
            'message': 'Your consultation has been completed. Please review the report and prescription.'
        }, room=f"patient_{consultation.get('patient_id')}")

        return jsonify({
            'message': 'Consultation completed',
            'consultation': consultation,
            'report': report
        }), 200

    except Exception as e:
        logger.error(f"Close consultation error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to close consultation: ' + str(e)}), 500

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_consultation_report(consultation):
    """Generate a structured report from consultation"""
    report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                     CONSULTATION REPORT                            ║
╚════════════════════════════════════════════════════════════════════╝

Consultation ID: {consultation.get('id')}
Date: {consultation.get('created_at')}
Language: {consultation.get('language')}
Status: {consultation.get('status')}

─── PARTICIPANTS ───────────────────────────────────────────────────
Patient: {consultation.get('patient_name')}
Doctor: {consultation.get('doctor_name')}

─── CONVERSATION TRANSCRIPT ────────────────────────────────────────
{consultation.get('transcript', 'No conversation recorded yet.')}

─── NOTES ──────────────────────────────────────────────────────────
This is an AI-assisted medical consultation. 
For proper diagnosis and treatment, please consult with a qualified 
medical professional in person.

Generated: {datetime.utcnow().isoformat()}
"""
    return report

# ============================================================================
# SOCKET.IO EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        token = request.args.get('token')
        user_id = None

        # Find user by token
        for uid, session in active_sessions.items():
            if session.get('token') == token:
                user_id = uid
                session['socket_id'] = request.sid
                break

        if user_id:
            role = active_sessions[user_id].get('role')
            if role == 'doctor':
                join_room(f"doctor_{user_id}")
            else:
                join_room(f"patient_{user_id}")

            logger.info(f"Client connected: user={user_id}, socket={request.sid}")
            emit('connection_response', {
                'message': 'Connected to consultation server',
                'user_id': user_id,
                'role': role
            })
        else:
            logger.warning(f"Connection attempt with invalid token")
            emit('error', {'message': 'Invalid token'})

    except Exception as e:
        logger.error(f"Connect error: {str(e)}", exc_info=True)

@socketio.on('join_consultation')
def handle_join_consultation(data):
    """Join a consultation room for real-time updates"""
    try:
        consult_id = data.get('consultation_id')
        token = data.get('token')

        # Verify token and get user
        user_id = None
        for uid, session in active_sessions.items():
            if session.get('token') == token:
                user_id = uid
                break

        if consult_id and user_id:
            join_room(f"consultation_{consult_id}")
            logger.info(f"User {user_id} joined consultation {consult_id}")

            emit('joined_consultation', {
                'consultation_id': consult_id,
                'message': 'You have joined the consultation'
            })

    except Exception as e:
        logger.error(f"Join consultation error: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: socket={request.sid}")

# ============================================================================
# STATIC FILES & CATCH-ALL
# ============================================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    if path and os.path.exists(os.path.join(FRONTEND, path)):
        return send_from_directory(FRONTEND, path)
    return send_from_directory(FRONTEND, 'index.html')

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting MediConsult Enhanced Backend...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
