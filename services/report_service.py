"""
Report Service — Generate and retrieve medical reports.
"""

from database import get_db, dict_from_row
from services.ai_engine import analyze_symptoms, suggest_diet, generate_disclaimer
import json


def generate_report(consultation_id):
    """Auto-generate a medical report from consultation data."""
    db = get_db()
    try:
        # Get consultation transcript
        consultation = db.execute(
            "SELECT * FROM consultations WHERE id = ?", (consultation_id,)
        ).fetchone()
        if not consultation:
            return {'error': 'Consultation not found'}

        consultation = dict_from_row(consultation)
        transcript = consultation.get('transcript', '')

        # AI analysis
        analysis = analyze_symptoms(transcript)
        symptoms_list = analysis.get('symptoms', [])
        diet_info = suggest_diet(analysis.get('diagnosis', ''), symptoms=symptoms_list)
        disclaimer = generate_disclaimer(analysis.get('confidence', 0))

        # Get prescription if exists
        prescription = db.execute(
            "SELECT medicines_json FROM prescriptions WHERE consultation_id = ?",
            (consultation_id,)
        ).fetchone()
        medication_text = ''
        if prescription:
            medicines = json.loads(prescription['medicines_json']) if prescription['medicines_json'] else []
            medication_text = '; '.join([
                f"{m.get('name', '')} {m.get('dosage', '')} - {m.get('frequency', '')}"
                for m in medicines
            ])

        # Check if report already exists
        existing = db.execute(
            "SELECT id FROM reports WHERE consultation_id = ?", (consultation_id,)
        ).fetchone()

        report_data = {
            'problem': analysis.get('problem', 'Patient consultation recorded'),
            'symptoms': ', '.join(analysis.get('symptoms', [])),
            'disease': analysis.get('diagnosis', 'Under evaluation'),
            'cause': analysis.get('cause', 'To be determined after further tests'),
            'medication': medication_text,
            'precautions': '; '.join(analysis.get('precautions', [])),
            'diet_suggestions': '; '.join(diet_info.get('diet', [])),
            'exercise_suggestions': '; '.join(diet_info.get('exercise', [])),
            'disclaimer': disclaimer,
            'ai_confidence': analysis.get('confidence', 0)
        }

        if existing:
            db.execute("""
                UPDATE reports SET problem=?, symptoms=?, disease=?, cause=?,
                medication=?, precautions=?, diet_suggestions=?, exercise_suggestions=?,
                disclaimer=?, ai_confidence=?
                WHERE consultation_id=?
            """, (*report_data.values(), consultation_id))
        else:
            db.execute("""
                INSERT INTO reports (consultation_id, problem, symptoms, disease, cause,
                medication, precautions, diet_suggestions, exercise_suggestions,
                disclaimer, ai_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (consultation_id, *report_data.values()))

        db.commit()
        report_data['consultation_id'] = consultation_id
        return {'success': True, 'report': report_data}

    finally:
        db.close()


def get_report(consultation_id):
    """Get a report for a consultation."""
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM reports WHERE consultation_id = ?", (consultation_id,)
        ).fetchone()
        return dict_from_row(row)
    finally:
        db.close()


def get_patient_reports(patient_id):
    """Get all reports for a patient."""
    db = get_db()
    try:
        rows = db.execute("""
            SELECT r.*, c.created_at as consultation_date, u.name as doctor_name
            FROM reports r
            JOIN consultations c ON r.consultation_id = c.id
            JOIN doctors d ON c.doctor_id = d.id
            JOIN users u ON d.user_id = u.id
            WHERE c.patient_id = ?
            ORDER BY r.created_at DESC
        """, (patient_id,)).fetchall()
        return [dict_from_row(r) for r in rows]
    finally:
        db.close()
