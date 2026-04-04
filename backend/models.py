from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    first_name    = db.Column(db.String(120), nullable=False)
    last_name     = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False)   # 'patient' or 'doctor'
    age           = db.Column(db.Integer, nullable=True)
    blood_group   = db.Column(db.String(10), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor_profile   = db.relationship('Doctor', backref='user', uselist=False, cascade='all,delete')
    sent_notifs      = db.relationship('Notification', foreign_keys='Notification.patient_id', backref='patient', lazy='dynamic')
    received_notifs  = db.relationship('Notification', foreign_keys='Notification.doctor_id',  backref='doctor',  lazy='dynamic')
    patient_consults = db.relationship('Consultation', foreign_keys='Consultation.patient_id', backref='patient_user', lazy='dynamic')
    doctor_consults  = db.relationship('Consultation', foreign_keys='Consultation.doctor_id',  backref='doctor_user',  lazy='dynamic')
    messages         = db.relationship('Message', backref='sender_user', lazy='dynamic')

    def to_dict(self):
        return {
            'id':          self.id,
            'first_name':  self.first_name,
            'last_name':   self.last_name,
            'email':       self.email,
            'role':        self.role,
            'age':         self.age,
            'blood_group': self.blood_group,
            'created_at':  self.created_at.isoformat()
        }


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    specialization      = db.Column(db.String(120), nullable=False)
    years_of_experience = db.Column(db.Integer, nullable=False, default=0)
    nmc_id              = db.Column(db.String(60), nullable=True)
    nmc_verified        = db.Column(db.Boolean, default=False)
    availability_status = db.Column(db.Boolean, default=False)
    average_rating      = db.Column(db.Float, default=0.0)
    total_ratings       = db.Column(db.Integer, default=0)
    bio                 = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id':                  self.id,
            'user_id':             self.user_id,
            'name':                f"{self.user.first_name} {self.user.last_name}" if self.user else '',
            'email':               self.user.email if self.user else '',
            'specialization':      self.specialization,
            'years_of_experience': self.years_of_experience,
            'nmc_id':              self.nmc_id,
            'nmc_verified':        self.nmc_verified,
            'availability_status': self.availability_status,
            'average_rating':      self.average_rating,
            'total_ratings':       self.total_ratings,
            'bio':                 self.bio
        }


class Consultation(db.Model):
    __tablename__ = 'consultations'
    id          = db.Column(db.Integer, primary_key=True)
    patient_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time  = db.Column(db.DateTime, nullable=True)
    end_time    = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    voice_transcript_patient = db.Column(db.Text, nullable=True)
    voice_transcript_doctor  = db.Column(db.Text, nullable=True)
    medical_report_doctor_notes = db.Column(db.Text, nullable=True)
    medical_report_patient_notes = db.Column(db.Text, nullable=True)
    ai_analysis_report = db.Column(db.Text, nullable=True)
    doctor_approved_report = db.Column(db.Boolean, default=False)
    language    = db.Column(db.String(20), default='en')
    status      = db.Column(db.String(20), default='pending')   # pending | active | completed
    messages    = db.relationship('Message', backref='consultation', lazy='dynamic', cascade='all,delete')

    def to_dict(self):
        return {
            'id':           self.id,
            'patient_id':   self.patient_id,
            'doctor_id':    self.doctor_id,
            'patient_name': f"{self.patient_user.first_name} {self.patient_user.last_name}" if self.patient_user else '',
            'doctor_name':  f"{self.doctor_user.first_name} {self.doctor_user.last_name}"  if self.doctor_user  else '',
            'created_at':   self.created_at.isoformat(),
            'start_time':   self.start_time.isoformat() if self.start_time else None,
            'end_time':     self.end_time.isoformat() if self.end_time else None,
            'voice_transcript_patient': self.voice_transcript_patient,
            'voice_transcript_doctor':  self.voice_transcript_doctor,
            'medical_report_doctor_notes': self.medical_report_doctor_notes,
            'medical_report_patient_notes': self.medical_report_patient_notes,
            'ai_analysis_report': self.ai_analysis_report,
            'doctor_approved_report': self.doctor_approved_report,
            'language':     self.language,
            'status':       self.status
        }


class MedicalHistory(db.Model):
    __tablename__ = 'medical_history'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True) # JSON/Text for medicine, duration, dosage
    dietary_plan = db.Column(db.Text, nullable=True)
    exercise_chart = db.Column(db.Text, nullable=True)
    treatment_advice = db.Column(db.Text, nullable=True)
    immunization_data = db.Column(db.Text, nullable=True)
    pregnancy_data = db.Column(db.Text, nullable=True)
    risk_indicators = db.Column(db.Text, nullable=True)
    injury_mobility_details = db.Column(db.Text, nullable=True)
    ent_findings = db.Column(db.Text, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('User', foreign_keys=[patient_id], backref='medical_records')
    consultation = db.relationship('Consultation', backref='medical_history_record')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'consultation_id': self.consultation_id,
            'diagnosis': self.diagnosis,
            'prescription': self.prescription,
            'dietary_plan': self.dietary_plan,
            'exercise_chart': self.exercise_chart,
            'treatment_advice': self.treatment_advice,
            'immunization_data': self.immunization_data,
            'pregnancy_data': self.pregnancy_data,
            'risk_indicators': self.risk_indicators,
            'injury_mobility_details': self.injury_mobility_details,
            'ent_findings': self.ent_findings,
            'recorded_at': self.recorded_at.isoformat()
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    doctor_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message    = db.Column(db.String(512), nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notif_type = db.Column(db.String(40), default='consultation_request')

    def to_dict(self):
        return {
            'id':           self.id,
            'doctor_id':    self.doctor_id,
            'patient_id':   self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}" if self.patient else '',
            'message':      self.message,
            'is_read':      self.is_read,
            'created_at':   self.created_at.isoformat(),
            'notif_type':   self.notif_type
        }


class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1-5
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('User', foreign_keys=[patient_id], backref='given_ratings')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='received_ratings')
    consultation = db.relationship('Consultation', backref='rating_feedback', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'consultation_id': self.consultation_id,
            'rating': self.rating,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat()
        }


class Message(db.Model):
    __tablename__ = 'messages'
    id              = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null = AI
    sender_role     = db.Column(db.String(20), nullable=False)  # 'patient' | 'ai'
    content         = db.Column(db.Text, nullable=False)
    language        = db.Column(db.String(10), default='en')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':              self.id,
            'consultation_id': self.consultation_id,
            'sender_role':     self.sender_role,
            'content':         self.content,
            'language':        self.language,
            'created_at':      self.created_at.isoformat()
        }
