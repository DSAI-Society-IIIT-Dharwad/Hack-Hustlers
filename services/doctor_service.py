"""
Doctor Service — Listing, Availability, Notifications
"""

from database import get_db, dict_from_row


def list_doctors():
    """Get all doctors with user info and availability."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT d.id as doctor_id, u.name, u.email, d.specialization,
                   d.experience_years, d.available, d.notified_patient_id
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.available DESC, u.name ASC
        """).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        db.close()


def get_doctor(doctor_id):
    """Get a single doctor's details."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT d.id as doctor_id, u.id as user_id, u.name, u.email,
                   d.specialization, d.experience_years, d.available
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            WHERE d.id = ?
        """, (doctor_id,)).fetchone()
        return dict_from_row(row)
    finally:
        db.close()


def get_doctor_by_user_id(user_id):
    """Get doctor record by user_id."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT d.id as doctor_id, u.id as user_id, u.name, u.email,
                   d.specialization, d.experience_years, d.available
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            WHERE d.user_id = ?
        """, (user_id,)).fetchone()
        return dict_from_row(row)
    finally:
        db.close()


def set_availability(doctor_id, available):
    """Toggle doctor availability (1 = available, 0 = unavailable)."""
    db = get_db()
    try:
        db.execute("UPDATE doctors SET available = ? WHERE id = ?", (1 if available else 0, doctor_id))
        db.commit()
        return {'success': True, 'available': available}
    finally:
        db.close()


def notify_doctor(doctor_id, patient_id):
    """Mark a doctor as being approached by a patient."""
    db = get_db()
    try:
        doctor = db.execute("SELECT available FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
        if not doctor:
            return {'error': 'Doctor not found'}
        if not doctor['available']:
            return {'error': 'Doctor is currently unavailable. Please select another doctor.'}

        db.execute(
            "UPDATE doctors SET notified_patient_id = ? WHERE id = ?",
            (patient_id, doctor_id)
        )
        db.commit()

        # Get patient name for notification
        patient_user = db.execute("""
            SELECT u.name FROM patients p JOIN users u ON p.user_id = u.id WHERE p.id = ?
        """, (patient_id,)).fetchone()

        return {
            'success': True,
            'message': f'Doctor notified. Patient: {patient_user["name"] if patient_user else "Unknown"}'
        }
    finally:
        db.close()


def get_pending_notifications(doctor_id):
    """Check if a doctor has pending patient notifications."""
    db = get_db()
    try:
        doctor = db.execute("SELECT notified_patient_id FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
        if not doctor or not doctor['notified_patient_id']:
            return {'has_notification': False}

        patient = db.execute("""
            SELECT p.id, u.name, p.age, p.gender, p.blood_group
            FROM patients p JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (doctor['notified_patient_id'],)).fetchone()

        return {
            'has_notification': True,
            'patient': dict_from_row(patient) if patient else None
        }
    finally:
        db.close()


def clear_notification(doctor_id):
    """Clear pending notification for a doctor."""
    db = get_db()
    try:
        db.execute("UPDATE doctors SET notified_patient_id = NULL WHERE id = ?", (doctor_id,))
        db.commit()
        return {'success': True}
    finally:
        db.close()
