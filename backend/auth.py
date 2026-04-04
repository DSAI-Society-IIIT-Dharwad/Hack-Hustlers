import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db, User, Doctor

auth_bp = Blueprint('auth', __name__)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()

    required = ['first_name', 'last_name', 'email', 'password', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    role = data['role']
    if role not in ('patient', 'doctor'):
        return jsonify({'error': 'Role must be patient or doctor'}), 400

    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        name=data['name'].strip(),
        email=data['email'].lower().strip(),
        password_hash=hash_password(data['password']),
        role=role,
        age=data.get('age'),
        blood_group=data.get('blood_group')
    )
    db.session.add(user)
    db.session.flush()   # get user.id before committing

    if role == 'doctor':
        # Simulate NMC verification: NMC IDs starting with 'NMC' are auto-verified
        nmc_id = data.get('nmc_id', '').strip()
        nmc_verified = nmc_id.upper().startswith('NMC') and len(nmc_id) >= 8

        doctor = Doctor(
            user_id=user.id,
            specialization=data.get('specialization', 'General Medicine'),
            years_of_experience=int(data.get('years_of_experience', 0)),
            nmc_id=nmc_id,
            nmc_verified=nmc_verified,
            is_available=True,
            bio=data.get('bio', '')
        )
        db.session.add(doctor)

    db.session.commit()

    token = create_access_token(identity={
        'id': user.id,
        'role': user.role,
        'name': user.name
    })

    return jsonify({
        'message': 'Account created successfully',
        'token': token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email    = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_access_token(identity={
        'id': user.id,
        'role': user.role,
        'name': user.name
    })

    user_data = user.to_dict()
    if user.role == 'doctor' and user.doctor_profile:
        user_data['doctor'] = user.doctor_profile.to_dict()

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user_data
    }), 200
