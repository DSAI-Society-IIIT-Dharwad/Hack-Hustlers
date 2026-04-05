"""
Prescription Service — Create, verify, approve prescriptions.
"""

from database import get_db, dict_from_row
import json
from services.ai_engine import translate_text


def create_prescription(consultation_id, medicines, diet='', exercise='', notes=''):
    """
    Create or update a prescription for a consultation.
    medicines: list of dicts [{name, dosage, frequency, duration}]
    """
    db = get_db()
    try:
        # Get patient's preferred language
        patient_lang = 'en'  # default
        try:
            consultation = db.execute(
                "SELECT p.preferred_language FROM consultations c "
                "JOIN patients p ON c.patient_id = p.id "
                "WHERE c.id = ?",
                (consultation_id,)
            ).fetchone()
            if consultation:
                patient_lang = consultation['preferred_language'] or 'en'
        except:
            pass  # Use default if query fails

        existing = db.execute(
            "SELECT id FROM prescriptions WHERE consultation_id = ?",
            (consultation_id,)
        ).fetchone()

        medicines_json = json.dumps(medicines) if isinstance(medicines, list) else medicines

        # Generate translations
        medicines_translated = translate_prescription_content(medicines, patient_lang) if medicines else ''
        diet_translated = translate_text(diet, 'en', patient_lang) if diet else ''
        exercise_translated = translate_text(exercise, 'en', patient_lang) if exercise else ''
        notes_translated = translate_text(notes, 'en', patient_lang) if notes else ''

        if existing:
            db.execute("""
                UPDATE prescriptions
                SET medicines_json = ?, diet = ?, exercise = ?, additional_notes = ?, approved = 0,
                    patient_language = ?, medicines_translated = ?, diet_translated = ?,
                    exercise_translated = ?, notes_translated = ?
                WHERE consultation_id = ?
            """, (medicines_json, diet, exercise, notes, patient_lang, medicines_translated,
                  diet_translated, exercise_translated, notes_translated, consultation_id))
        else:
            db.execute("""
                INSERT INTO prescriptions (
                    consultation_id, medicines_json, diet, exercise, additional_notes,
                    patient_language, medicines_translated, diet_translated,
                    exercise_translated, notes_translated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (consultation_id, medicines_json, diet, exercise, notes, patient_lang,
                  medicines_translated, diet_translated, exercise_translated, notes_translated))

        db.commit()
        return {'success': True}
    finally:
        db.close()


def translate_prescription_content(medicines, target_lang):
    """Translate medicine list into target language."""
    if not medicines or target_lang == 'en':
        return ''

    try:
        translated_meds = []
        for med in medicines:
            name_translated = translate_text(med.get('name', ''), 'en', target_lang)
            dosage_translated = translate_text(med.get('dosage', ''), 'en', target_lang)
            frequency_translated = translate_text(med.get('frequency', ''), 'en', target_lang)
            duration_translated = translate_text(med.get('duration', ''), 'en', target_lang)

            translated_meds.append({
                'name': name_translated,
                'dosage': dosage_translated,
                'frequency': frequency_translated,
                'duration': duration_translated
            })

        return json.dumps(translated_meds)
    except:
        return ''


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
            result['medicines_translated'] = json.loads(result['medicines_translated']) if result['medicines_translated'] else []
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
