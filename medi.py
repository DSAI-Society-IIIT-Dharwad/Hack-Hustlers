"""
Database helper module — SQLite connection management and initialization.
"""

import os
import sqlite3
from config import Config


def get_db():
    """Get a database connection with row factory enabled."""
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database from schema.sql and seed demo data."""
    conn = get_db()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()

    # Check if demo data already exists
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_demo_data(conn)

    conn.close()


def seed_demo_data(conn):
    """Populate database with sample doctors and a demo patient."""
    import bcrypt

    demo_password = bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # ── Demo Doctors ──
    doctors = [
        ('Dr. Arun Sharma', 'dr.sharma@hospital.com', 'Cardiology', 15),
        ('Dr. Priya Patel', 'dr.patel@hospital.com', 'General Medicine', 10),
        ('Dr. Rajesh Kumar', 'dr.kumar@hospital.com', 'Neurology', 12),
        ('Dr. Sneha Reddy', 'dr.reddy@hospital.com', 'Pediatrics', 8),
        ('Dr. Mohammed Ali', 'dr.ali@hospital.com', 'Orthopedics', 20),
        ('Dr. Kavitha Nair', 'dr.nair@hospital.com', 'Dermatology', 7),
        ('Dr. Sanjay Gupta', 'dr.gupta@hospital.com', 'ENT', 11),
        ('Dr. Fatima Sheikh', 'dr.sheikh@hospital.com', 'Gynecology', 14),
    ]

    for name, email, spec, exp in doctors:
        conn.execute(
            "INSERT INTO users (role, name, email, password_hash) VALUES (?, ?, ?, ?)",
            ('doctor', name, email, demo_password)
        )
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO doctors (user_id, specialization, experience_years, available) VALUES (?, ?, ?, ?)",
            (user_id, spec, exp, 1)
        )

    # ── Demo Patient ──
    conn.execute(
        "INSERT INTO users (role, name, email, password_hash) VALUES (?, ?, ?, ?)",
        ('patient', 'Rahul Verma', 'rahul@patient.com', demo_password)
    )
    patient_user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO patients (user_id, age, gender, blood_group) VALUES (?, ?, ?, ?)",
        (patient_user_id, 28, 'Male', 'B+')
    )

    conn.commit()
    print("✅ Demo data seeded successfully")


def dict_from_row(row):
    """Convert a sqlite3.Row to a dictionary."""
    if row is None:
        return None
    return dict(row)
