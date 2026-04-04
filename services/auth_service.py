"""
Authentication Service — Registration, Login, JWT Token Management
"""

import bcrypt
import jwt
import datetime
from database import get_db, dict_from_row
from config import Config


def register_user(name, email, password, role, **extra):
    """
    Register a new user (patient or doctor).
    Returns: dict with user info and token, or error string.
    """
    if role not in ('patient', 'doctor'):
        return {'error': 'Invalid role. Must be patient or doctor.'}

    db = get_db()
    try:
        # Check if email already exists
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return {'error': 'Email already registered.'}

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert user
        db.execute(
            "INSERT INTO users (role, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (role, name, email, password_hash)
        )
        user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Create role-specific record
        if role == 'doctor':
            specialization = extra.get('specialization', 'General Medicine')
            experience = extra.get('experience_years', 0)
            db.execute(
                "INSERT INTO doctors (user_id, specialization, experience_years) VALUES (?, ?, ?)",
                (user_id, specialization, experience)
            )
        else:
            age = extra.get('age')
            gender = extra.get('gender')
            blood_group = extra.get('blood_group')
            db.execute(
                "INSERT INTO patients (user_id, age, gender, blood_group) VALUES (?, ?, ?, ?)",
                (user_id, age, gender, blood_group)
            )

        db.commit()

        # Retrieve the role-specific ID (needed immediately on the client)
        role_id = None
        if role == 'doctor':
            row = db.execute("SELECT id FROM doctors WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                role_id = row['id']
        else:
            row = db.execute("SELECT id FROM patients WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                role_id = row['id']

        # Generate JWT
        token = generate_token(user_id, role, name)

        return {
            'success': True,
            'user': {
                'id': user_id,
                'name': name,
                'email': email,
                'role': role,
                'role_id': role_id      # ← critical: used for consultation & notification routing
            },
            'token': token
        }

    except Exception as e:
        db.rollback()
        return {'error': str(e)}
    finally:
        db.close()


def login_user(email, password):
    """
    Authenticate user and return JWT token.
    """
    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            return {'error': 'Invalid email or password.'}

        user = dict_from_row(user)

        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return {'error': 'Invalid email or password.'}

        token = generate_token(user['id'], user['role'], user['name'])

        # Get role-specific ID
        role_id = None
        if user['role'] == 'doctor':
            doc = db.execute("SELECT id FROM doctors WHERE user_id = ?", (user['id'],)).fetchone()
            if doc:
                role_id = doc['id']
        else:
            pat = db.execute("SELECT id FROM patients WHERE user_id = ?", (user['id'],)).fetchone()
            if pat:
                role_id = pat['id']

        return {
            'success': True,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'role_id': role_id
            },
            'token': token
        }

    finally:
        db.close()


def generate_token(user_id, role, name):
    """Generate a JWT token."""
    payload = {
        'user_id': user_id,
        'role': role,
        'name': name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def verify_token(token):
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return {'valid': True, 'payload': payload}
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'valid': False, 'error': 'Invalid token'}


def get_user_profile(user_id):
    """Get full user profile with role-specific data."""
    db = get_db()
    try:
        user = dict_from_row(db.execute("SELECT id, role, name, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone())
        if not user:
            return None

        if user['role'] == 'doctor':
            doc = dict_from_row(db.execute("SELECT * FROM doctors WHERE user_id = ?", (user_id,)).fetchone())
            user['profile'] = doc
        else:
            pat = dict_from_row(db.execute("SELECT * FROM patients WHERE user_id = ?", (user_id,)).fetchone())
            user['profile'] = pat

        return user
    finally:
        db.close()
