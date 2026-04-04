-- ============================================================
-- Secure AI-Powered Multilingual Telemedicine System
-- Database Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL CHECK(role IN ('patient', 'doctor')),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    specialization TEXT NOT NULL DEFAULT 'General Medicine',
    experience_years INTEGER DEFAULT 0,
    available INTEGER DEFAULT 1,
    notified_patient_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    age INTEGER,
    gender TEXT,
    blood_group TEXT,
    medical_history TEXT DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    transcript TEXT DEFAULT '',
    original_language TEXT DEFAULT 'en',
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'cancelled')),
    urgency_level TEXT DEFAULT 'low' CHECK(urgency_level IN ('low', 'medium', 'high', 'critical')),
    urgency_keywords TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id INTEGER NOT NULL,
    medicines_json TEXT DEFAULT '[]',
    diet TEXT DEFAULT '',
    exercise TEXT DEFAULT '',
    additional_notes TEXT DEFAULT '',
    approved INTEGER DEFAULT 0,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id INTEGER NOT NULL,
    problem TEXT DEFAULT '',
    symptoms TEXT DEFAULT '',
    disease TEXT DEFAULT '',
    cause TEXT DEFAULT '',
    medication TEXT DEFAULT '',
    precautions TEXT DEFAULT '',
    diet_suggestions TEXT DEFAULT '',
    exercise_suggestions TEXT DEFAULT '',
    disclaimer TEXT DEFAULT '',
    ai_confidence REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_consultations_patient ON consultations(patient_id);
CREATE INDEX IF NOT EXISTS idx_consultations_doctor ON consultations(doctor_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_consultation ON prescriptions(consultation_id);
CREATE INDEX IF NOT EXISTS idx_reports_consultation ON reports(consultation_id);
