"""
Prescription Service — Create, verify, approve prescriptions.
"""

from database import get_db, dict_from_row
import json


def create_prescription(consultation_id, medicines, diet='', exercise='', notes=''):
    """
    Create or update a prescription for a consultation.
    medicines: list of dicts [{name, dosage, frequency, duration}]
    """
    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM prescriptions WHERE consultation_id = ?",
            (consultation_id,)
        ).fetchone()

        medicines_json = json.dumps(medicines) if isinstance(medicines, list) else medicines

        if existing:
            db.execute("""
                UPDATE prescriptions
                SET medicines_json = ?, diet = ?, exercise = ?, additional_notes = ?, approved = 0
                WHERE consultation_id = ?
            """, (medicines_json, diet, exercise, notes, consultation_id))
        else:
            db.execute("""
                INSERT INTO prescriptions (consultation_id, medicines_json, diet, exercise, additional_notes)
                VALUES (?, ?, ?, ?, ?)
            """, (consultation_id, medicines_json, diet, exercise, notes))

        db.commit()
        return {'success': True}
    finally:
        db.close()


def approve_prescription(prescription_id):
    """Doctor approves the prescription — makes it visible to patient."""
    db = get_db()
    try:
        db.execute(
            "UPDATE prescriptions SET approved = 1, approved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (prescription_id,)
        )
        db.commit()
        return {'success': True}
    finally:
        db.close()


def get_prescription(consultation_id, require_approved=False):
    """Get prescription for a consultation."""
    db = get_db()
    try:
        query = "SELECT * FROM prescriptions WHERE consultation_id = ?"
        if require_approved:
            query += " AND approved = 1"
        row = db.execute(query, (consultation_id,)).fetchone()
        if row:
            result = dict_from_row(row)
            result['medicines'] = json.loads(result['medicines_json']) if result['medicines_json'] else []
            return result
        return None
    finally:
        db.close()


def get_prescription_by_id(prescription_id):
    """Get prescription by its own ID."""
    db = get_db()
    try:
        row = db.execute("SELECT * FROM prescriptions WHERE id = ?", (prescription_id,)).fetchone()
        if row:
            result = dict_from_row(row)
            result['medicines'] = json.loads(result['medicines_json']) if result['medicines_json'] else []
            return result
        return None
    finally:
        db.close()
