from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
import os
import json
from datetime import datetime

app = Flask(__name__, static_folder=str(Path(__file__).parent.parent / 'frontend'), static_url_path='/static')

FRONTEND = Path(__file__).parent.parent / 'frontend'

# Mock data storage (in-memory for demo)
mock_users = []
mock_doctors = []
mock_patients = []
mock_consultations = []
mock_messages = []

# Initialize with sample doctors
def init_sample_doctors():
    if not mock_doctors:
        sample_doctors = [
            {
                'id': 1001,
                'user_id': 1001,
                'specialization': 'Cardiologist',
                'years_of_experience': 12,
                'nmc_id': 'NMC20034521',
                'nmc_verified': True,
                'is_available': True,
                'bio': 'Expert in heart diseases with 12+ years of experience.'
            },
            {
                'id': 1002,
                'user_id': 1002,
                'specialization': 'Neurologist',
                'years_of_experience': 8,
                'nmc_id': 'NMC18027834',
                'nmc_verified': True,
                'is_available': False,
                'bio': 'Specialist in brain and nervous system disorders.'
            },
            {
                'id': 1003,
                'user_id': 1003,
                'specialization': 'Dermatologist',
                'years_of_experience': 5,
                'nmc_id': 'NMC21045678',
                'nmc_verified': True,
                'is_available': True,
                'bio': 'Skin specialist with expertise in cosmetic dermatology.'
            }
        ]

        sample_users = [
            {'id': 1001, 'name': 'Dr. Priya Sharma', 'email': 'priya@medic.com', 'role': 'doctor'},
            {'id': 1002, 'name': 'Dr. Rajan Mehta', 'email': 'rajan@medic.com', 'role': 'doctor'},
            {'id': 1003, 'name': 'Dr. Ananya Rao', 'email': 'ananya@medic.com', 'role': 'doctor'}
        ]

        mock_doctors.extend(sample_doctors)
        mock_users.extend(sample_users)

init_sample_doctors()

# Simple token validation
def validate_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header.replace('Bearer ', '')
    if not token.startswith('mock_jwt_token_'):
        return None

    # Extract user info from token
    parts = token.split('_')
    if len(parts) < 4:
        return None

    user_id = int(parts[3])
    role = parts[4] if len(parts) > 4 else None

    user = next((u for u in mock_users if u['id'] == user_id), None)
    return user if user and user['role'] == role else None

# Mock API endpoints for demo
@app.route('/api/auth/signup', methods=['POST'])
def mock_signup():
    data = request.get_json()

    # Check if email already exists
    if any(u['email'] == data['email'] for u in mock_users):
        return jsonify({'error': 'Email already registered'}), 409

    # Create mock user
    user = {
        'id': len(mock_users) + 1,
        'name': data['name'],
        'email': data['email'],
        'role': data['role'],
        'age': data.get('age'),
        'blood_group': data.get('blood_group'),
        'created_at': datetime.utcnow().isoformat()
    }

    mock_users.append(user)

    # Add role-specific data
    if data['role'] == 'doctor':
        doctor = {
            'id': len(mock_doctors) + 1,
            'user_id': user['id'],
            'specialization': data.get('specialization', 'General Medicine'),
            'years_of_experience': data.get('years_of_experience', 0),
            'nmc_id': data.get('nmc_id', ''),
            'nmc_verified': data.get('nmc_id', '').upper().startswith('NMC'),
            'is_available': True,
            'bio': data.get('bio', '')
        }
        mock_doctors.append(doctor)
        user['doctor'] = doctor
    else:
        mock_patients.append({
            'user_id': user['id'],
            'age': data.get('age'),
            'blood_group': data.get('blood_group')
        })

    # Mock JWT token
    token = f"mock_jwt_token_{user['id']}_{data['role']}"

    return jsonify({
        'message': 'Account created successfully',
        'token': token,
        'user': user
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def mock_login():
    data = request.get_json()
    email = data.get('email', '').lower().strip()

    # Find user
    user = next((u for u in mock_users if u['email'] == email), None)
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    # Mock successful login
    token = f"mock_jwt_token_{user['id']}_{user['role']}"

    user_data = user.copy()
    if user['role'] == 'doctor':
        doctor = next((d for d in mock_doctors if d['user_id'] == user['id']), None)
        if doctor:
            user_data['doctor'] = doctor

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user_data
    }), 200

@app.route('/api/patient/doctors', methods=['GET'])
def mock_get_doctors():
    # Return mock doctors
    doctors = []
    for doctor in mock_doctors:
        user = next((u for u in mock_users if u['id'] == doctor['user_id']), None)
        if user:
            doctor_data = doctor.copy()
            doctor_data.update({
                'name': user['name'],
                'email': user['email']
            })
            doctors.append(doctor_data)

    return jsonify(doctors), 200

@app.route('/api/doctor/profile', methods=['GET'])
def mock_doctor_profile():
    user = validate_token()
    if not user or user['role'] != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    doctor = next((d for d in mock_doctors if d['user_id'] == user['id']), None)
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    profile = user.copy()
    profile['doctor'] = doctor
    return jsonify(profile), 200

@app.route('/api/patient/profile', methods=['GET'])
def mock_patient_profile():
    user = validate_token()
    if not user or user['role'] != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify(user), 200

@app.route('/api/doctor/availability', methods=['PUT'])
def mock_toggle_availability():
    user = validate_token()
    if not user or user['role'] != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    doctor = next((d for d in mock_doctors if d['user_id'] == user['id']), None)
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404

    data = request.get_json()
    doctor['is_available'] = data.get('is_available', not doctor['is_available'])

    return jsonify({
        'message': 'Availability updated',
        'is_available': doctor['is_available']
    }), 200

@app.route('/api/doctor/notifications', methods=['GET'])
def mock_get_notifications():
    user = validate_token()
    if not user or user['role'] != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    # Return mock notifications
    notifications = [
        {
            'id': 1,
            'doctor_id': user['id'],
            'patient_id': 2,
            'message': 'New consultation request from John Doe (Age: 30, Blood Group: O+)',
            'is_read': False,
            'created_at': datetime.utcnow().isoformat(),
            'notif_type': 'consultation_request'
        }
    ]
    return jsonify(notifications), 200

@app.route('/api/doctor/consultations', methods=['GET'])
def mock_get_consultations():
    user = validate_token()
    if not user or user['role'] != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    # Return mock consultations
    consultations = [
        {
            'id': 1,
            'patient_id': 2,
            'doctor_id': user['id'],
            'patient_name': 'John Doe',
            'doctor_name': user['name'],
            'created_at': datetime.utcnow().isoformat(),
            'transcript': 'Patient described symptoms of headache and fever...',
            'report_text': 'Patient presented with mild headache and low-grade fever. Recommended rest and hydration. Follow up in 3 days if symptoms persist.',
            'language': 'en',
            'status': 'completed'
        }
    ]
    return jsonify(consultations), 200

@app.route('/api/patient/consultations', methods=['GET'])
def mock_patient_consultations():
    user = validate_token()
    if not user or user['role'] != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    # Return mock patient consultations
    consultations = [
        {
            'id': 1,
            'patient_id': user['id'],
            'doctor_id': 1001,
            'patient_name': user['name'],
            'doctor_name': 'Dr. Priya Sharma',
            'created_at': datetime.utcnow().isoformat(),
            'transcript': 'Patient described symptoms of headache and fever...',
            'report_text': 'Patient presented with mild headache and low-grade fever. Recommended rest and hydration. Follow up in 3 days if symptoms persist.',
            'language': 'en',
            'status': 'completed'
        }
    ]
    return jsonify(consultations), 200

@app.route('/api/patient/consult', methods=['POST'])
def mock_request_consultation():
    user = validate_token()
    if not user or user['role'] != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    doctor_id = data.get('doctor_id')
    language = data.get('language', 'en')

    doctor = next((d for d in mock_doctors if d['user_id'] == doctor_id), None)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404

    consultation = {
        'id': len(mock_consultations) + 1,
        'patient_id': user['id'],
        'doctor_id': doctor_id,
        'patient_name': user['name'],
        'doctor_name': next((u['name'] for u in mock_users if u['id'] == doctor_id), 'Unknown'),
        'language': language,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'report_text': None,
        'transcript': ''
    }
    mock_consultations.append(consultation)

    mock_messages.append({
        'id': len(mock_messages) + 1,
        'consultation_id': consultation['id'],
        'user_id': None,
        'sender_role': 'ai',
        'content': 'Your consultation request has been sent to the doctor. Please wait for confirmation.',
        'language': language,
        'created_at': datetime.utcnow().isoformat()
    })

    return jsonify({
        'message': 'Consultation requested successfully',
        'consultation': consultation,
        'welcome_message': 'Your consultation request has been sent to the doctor.'
    }), 201

@app.route('/api/patient/consultations/<int:consult_id>/messages', methods=['GET'])
def mock_patient_messages(consult_id):
    user = validate_token()
    if not user or user['role'] != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    consult = next((c for c in mock_consultations if c['id'] == consult_id and c['patient_id'] == user['id']), None)
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404

    messages = [m for m in mock_messages if m['consultation_id'] == consult_id]
    return jsonify(messages), 200

@app.route('/api/patient/consultations/<int:consult_id>/chat', methods=['POST'])
def mock_patient_chat(consult_id):
    user = validate_token()
    if not user or user['role'] != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    consult = next((c for c in mock_consultations if c['id'] == consult_id and c['patient_id'] == user['id']), None)
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404

    data = request.get_json()
    text = data.get('message', '').strip()
    if not text:
        return jsonify({'error': 'Message cannot be empty'}), 400

    user_msg = {
        'id': len(mock_messages) + 1,
        'consultation_id': consult_id,
        'user_id': user['id'],
        'sender_role': 'patient',
        'content': text,
        'language': consult['language'],
        'created_at': datetime.utcnow().isoformat()
    }
    mock_messages.append(user_msg)
    consult['transcript'] += f"Patient: {text}\n"

    ai_reply = {
        'id': len(mock_messages) + 1,
        'consultation_id': consult_id,
        'user_id': None,
        'sender_role': 'ai',
        'content': 'Thank you. Your message has been received and will be shared with the doctor once they respond.',
        'language': consult['language'],
        'created_at': datetime.utcnow().isoformat()
    }
    mock_messages.append(ai_reply)
    consult['transcript'] += f"AI: {ai_reply['content']}\n"

    return jsonify({
        'patient_message': user_msg,
        'ai_response': ai_reply
    }), 200

@app.route('/api/patient/consultations/<int:consult_id>/report', methods=['POST'])
def mock_patient_report(consult_id):
    user = validate_token()
    if not user or user['role'] != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    consult = next((c for c in mock_consultations if c['id'] == consult_id and c['patient_id'] == user['id']), None)
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404

    report = f"Consultation Report\nPatient: {consult['patient_name']}\nDoctor: {consult['doctor_name']}\nDate: {consult['created_at']}\n\nSummary:\n{consult['transcript'] or 'No conversation yet.'}\n\nStatus: {consult['status']}"
    consult['report_text'] = report
    consult['status'] = 'completed'

    return jsonify({
        'report': report,
        'consultation': consult
    }), 200

@app.route('/api/doctor/consultations/<int:consult_id>', methods=['GET'])
def mock_doctor_consultation(consult_id):
    user = validate_token()
    if not user or user['role'] != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    consult = next((c for c in mock_consultations if c['id'] == consult_id and c['doctor_id'] == user['id']), None)
    if not consult:
        return jsonify({'error': 'Consultation not found'}), 404

    messages = [m for m in mock_messages if m['consultation_id'] == consult_id]
    consult_data = consult.copy()
    consult_data['messages'] = messages
    return jsonify(consult_data), 200

@app.route('/api/doctor/notifications/mark-all-read', methods=['PUT'])
def mock_doctor_mark_all_read():
    user = validate_token()
    if not user or user['role'] != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({'message': 'All notifications marked as read'}), 200

# Static file serving
@app.route('/')
def index():
    return send_from_directory(FRONTEND, 'index.html')

@app.route('/doctor')
def doctor_page():
    return send_from_directory(FRONTEND, 'doctor_dashboard.html')

@app.route('/patient')
def patient_page():
    return send_from_directory(FRONTEND, 'patient_dashboard.html')

@app.route('/css/<path:filename>')
def css(filename):
    return send_from_directory(FRONTEND / 'css', filename)

@app.route('/js/<path:filename>')
def js(filename):
    return send_from_directory(FRONTEND / 'js', filename)

@app.route('/api/doctor/stats', methods=['GET'])
def mock_doctor_stats():
    user = validate_token()
    if not user or user['role'] != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    # Mock stats
    return jsonify({
        'total_consultations': 5,
        'completed': 4,
        'pending': 1,
        'unread_notifications': 2
    }), 200

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'MediConsult Demo Server running with mock APIs',
        'mock_data': {
            'users': len(mock_users),
            'doctors': len(mock_doctors),
            'patients': len(mock_patients)
        }
    }), 200

if __name__ == '__main__':
    print('\n✅  MediConsult Demo Server running at http://localhost:5000')
    print('🎭  Mock API endpoints enabled for signup/login testing')
    print('⚠️  Note: This is a demo with in-memory data. Full features require Python 3.12.\n')
    app.run(host='0.0.0.0', port=5000, debug=True)