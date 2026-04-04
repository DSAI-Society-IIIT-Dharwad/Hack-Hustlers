"""
Consultation Service — Start, update, complete consultations.
"""

from database import get_db, dict_from_row


def start_consultation(patient_id, doctor_id):
    """Create a new consultation session."""
    db = get_db()
    try:
        # Check if doctor is available
        doctor = db.execute("SELECT available FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
        if not doctor or not doctor['available']:
            return {'error': 'Doctor is not available.'}

        # Check for existing active consultation
        existing = db.execute("""
            SELECT id FROM consultations
            WHERE patient_id = ? AND doctor_id = ? AND status = 'active'
        """, (patient_id, doctor_id)).fetchone()
        if existing:
            return {'success': True, 'consultation_id': existing['id'], 'resumed': True}

        db.execute(
            "INSERT INTO consultations (patient_id, doctor_id, status) VALUES (?, ?, 'active')",
            (patient_id, doctor_id)
        )
        consultation_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.commit()

        return {'success': True, 'consultation_id': consultation_id, 'resumed': False}
    finally:
        db.close()


def append_transcript(consultation_id, speaker, text, language='en'):
    """Append a message to the consultation transcript."""
    db = get_db()
    try:
        current = db.execute(
            "SELECT transcript, original_language FROM consultations WHERE id = ?",
            (consultation_id,)
        ).fetchone()
        if not current:
            return {'error': 'Consultation not found'}

        existing = current['transcript'] or ''
        separator = '\n' if existing else ''
        new_entry = f"[{speaker.upper()}]: {text}"
        updated = existing + separator + new_entry

        db.execute(
            "UPDATE consultations SET transcript = ?, original_language = ? WHERE id = ?",
            (updated, language, consultation_id)
        )
        db.commit()
        return {'success': True}
    finally:
        db.close()


def update_urgency(consultation_id, urgency_level, keywords):
    """Update urgency level for a consultation."""
    db = get_db()
    try:
        db.execute(
            "UPDATE consultations SET urgency_level = ?, urgency_keywords = ? WHERE id = ?",
            (urgency_level, ','.join(keywords) if keywords else '', consultation_id)
        )
        db.commit()
        return {'success': True}
    finally:
        db.close()


def complete_consultation(consultation_id):
    """Mark a consultation as completed."""
    db = get_db()
    try:
        db.execute(
            "UPDATE consultations SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (consultation_id,)
        )
        db.commit()
        return {'success': True}
    finally:
        db.close()


def get_consultation(consultation_id):
    """Get full consultation details."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT c.*, u_p.name as patient_name, u_d.name as doctor_name,
                   d.specialization, p.age, p.gender, p.blood_group
            FROM consultations c
            JOIN patients p ON c.patient_id = p.id
            JOIN users u_p ON p.user_id = u_p.id
            JOIN doctors d ON c.doctor_id = d.id
            JOIN users u_d ON d.user_id = u_d.id
            WHERE c.id = ?
        """, (consultation_id,)).fetchone()
        return dict_from_row(row)
    finally:
        db.close()


def get_active_consultation_for_doctor(doctor_id):
    """Get the current active consultation for a doctor."""
    db = get_db()
    try:
        row = db.execute("""
            SELECT c.*, u_p.name as patient_name, p.age, p.gender, p.blood_group
            FROM consultations c
            JOIN patients p ON c.patient_id = p.id
            JOIN users u_p ON p.user_id = u_p.id
            WHERE c.doctor_id = ? AND c.status = 'active'
            ORDER BY c.created_at DESC
            LIMIT 1
        """, (doctor_id,)).fetchone()
        return dict_from_row(row)
    finally:
        db.close()


def get_patient_history(patient_id):
    """Get all past consultations for a patient."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT c.id, c.status, c.urgency_level, c.created_at, c.completed_at,
                   u_d.name as doctor_name, d.specialization,
                   r.disease, r.problem, r.symptoms
            FROM consultations c
            JOIN doctors d ON c.doctor_id = d.id
            JOIN users u_d ON d.user_id = u_d.id
            LEFT JOIN reports r ON r.consultation_id = c.id
            WHERE c.patient_id = ?
            ORDER BY c.created_at DESC
        """, (patient_id,)).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        db.close()


def get_doctor_history(doctor_id):
    """Get all past consultations for a doctor."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT c.id, c.status, c.urgency_level, c.created_at, c.completed_at,
                   u_p.name as patient_name, p.age, p.gender,
                   r.disease, r.problem, r.symptoms
            FROM consultations c
            JOIN patients p ON c.patient_id = p.id
            JOIN users u_p ON p.user_id = u_p.id
            LEFT JOIN reports r ON r.consultation_id = c.id
            WHERE c.doctor_id = ?
            ORDER BY c.created_at DESC
        """, (doctor_id,)).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        db.close()
