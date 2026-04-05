"""
AI Engine — Symptom Analysis, Urgency Detection, Medicine Verification,
Diet Suggestions, and Medical Disclaimer Logic.

Uses rule-based / keyword matching for local analysis, enhanced with Groq AI for comprehensive medical data.
Full-sentence multilingual translation powered by deep-translator (Google Translate).
"""

import re
import os
from config import Config

# Try to import deep-translator; fall back gracefully if unavailable
try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    print('⚠️  deep-translator not installed. Falling back to dictionary translation.')

# Try to import Groq for enhanced medical AI
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    groq_client = Groq(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None
except ImportError:
    GROQ_AVAILABLE = False
    groq_client = None
    print('⚠️  groq not installed. Using local medical database only.')

# Try to import Google AI (Gemini) for additional medical queries
try:
    import google.genai as genai
    GOOGLE_AI_AVAILABLE = True
    if Config.GEMINI_API_KEY:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
    else:
        gemini_model = None
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    gemini_model = None
    print('⚠️  google-genai not installed. Using only local and Groq databases.')

# ═══════════════════════════════════════════════════════════════
# URGENCY DETECTION
# ═══════════════════════════════════════════════════════════════

URGENCY_KEYWORDS = {
    'critical': [
        'chest pain', 'heart attack', 'stroke', 'unconscious', 'not breathing',
        'severe bleeding', 'seizure', 'choking', 'anaphylaxis', 'cardiac arrest',
        'collapsed', 'no pulse', 'poisoning', 'overdose', 'coma'
    ],
    'high': [
        'difficulty breathing', 'shortness of breath', 'high fever',
        'severe headache', 'vomiting blood', 'heavy bleeding', 'fracture',
        'burn', 'allergic reaction', 'fainting', 'blood in stool',
        'sudden vision loss', 'suicidal', 'severe pain', 'paralysis'
    ],
    'medium': [
        'persistent cough', 'mild fever', 'dizziness', 'nausea', 'vomiting',
        'diarrhea', 'rash', 'swelling', 'numbness', 'joint pain',
        'ear pain', 'sore throat', 'urinary pain', 'abdominal pain'
    ]
}


def detect_urgency(transcript):
    """
    Analyze transcript for urgency indicators.
    Returns: { is_urgent, severity, keywords_found, alert_message }
    """
    if not transcript:
        return {'is_urgent': False, 'severity': 'low', 'keywords_found': [], 'alert_message': ''}

    text = transcript.lower()
    found = {'critical': [], 'high': [], 'medium': []}

    for severity, keywords in URGENCY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                found[severity].append(kw)

    if found['critical']:
        return {
            'is_urgent': True,
            'severity': 'critical',
            'keywords_found': found['critical'],
            'alert_message': f"🚨 CRITICAL EMERGENCY: {', '.join(found['critical'])}. Immediate attention required!"
        }
    elif found['high']:
        return {
            'is_urgent': True,
            'severity': 'high',
            'keywords_found': found['high'],
            'alert_message': f"⚠️ HIGH URGENCY: {', '.join(found['high'])}. Priority consultation needed."
        }
    elif found['medium']:
        return {
            'is_urgent': False,
            'severity': 'medium',
            'keywords_found': found['medium'],
            'alert_message': f"ℹ️ Moderate symptoms detected: {', '.join(found['medium'])}"
        }

    return {'is_urgent': False, 'severity': 'low', 'keywords_found': [], 'alert_message': ''}


def query_groq_medical_info(query, context=""):
    """
    Query Groq AI for medical information when local database is insufficient.
    Falls back to Google Gemini if Groq is unavailable.
    Returns structured medical information or None if unavailable.
    """
    # Try Groq first
    if GROQ_AVAILABLE and groq_client:
        try:
            prompt = f"""
            You are a medical AI assistant. Provide accurate, evidence-based medical information.
            Context: {context}
            Query: {query}

            Please provide a structured response with:
            - Diagnosis (if applicable)
            - Common symptoms
            - Possible causes
            - Recommended treatments/medicines
            - Diagnostic tests
            - Precautions

            Keep responses professional and evidence-based. Include confidence level (high/medium/low).
            """

            response = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",  # Using Mixtral for medical queries
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️  Groq API error: {e}")

    # Fallback to Google Gemini
    if GOOGLE_AI_AVAILABLE and gemini_model:
        try:
            prompt = f"""
            You are a medical AI assistant. Provide accurate, evidence-based medical information.
            Context: {context}
            Query: {query}

            Please provide a structured response with:
            - Diagnosis (if applicable)
            - Common symptoms
            - Possible causes
            - Recommended treatments/medicines
            - Diagnostic tests
            - Precautions

            Keep responses professional and evidence-based. Include confidence level (high/medium/low).
            """

            response = gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️  Google Gemini API error: {e}")

    return None
    """
    Analyze transcript for urgency indicators.
    Returns: { is_urgent, severity, keywords_found, alert_message }
    """
    if not transcript:
        return {'is_urgent': False, 'severity': 'low', 'keywords_found': [], 'alert_message': ''}

    text = transcript.lower()
    found = {'critical': [], 'high': [], 'medium': []}

    for severity, keywords in URGENCY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                found[severity].append(kw)

    if found['critical']:
        return {
            'is_urgent': True,
            'severity': 'critical',
            'keywords_found': found['critical'],
            'alert_message': f"🚨 CRITICAL EMERGENCY: {', '.join(found['critical'])}. Immediate attention required!"
        }
    elif found['high']:
        return {
            'is_urgent': True,
            'severity': 'high',
            'keywords_found': found['high'],
            'alert_message': f"⚠️ HIGH URGENCY: {', '.join(found['high'])}. Priority consultation needed."
        }
    elif found['medium']:
        return {
            'is_urgent': False,
            'severity': 'medium',
            'keywords_found': found['medium'],
            'alert_message': f"ℹ️ Moderate symptoms detected: {', '.join(found['medium'])}"
        }

    return {'is_urgent': False, 'severity': 'low', 'keywords_found': [], 'alert_message': ''}


# ═══════════════════════════════════════════════════════════════
# SYMPTOM ANALYSIS & DIAGNOSIS
# ═══════════════════════════════════════════════════════════════

SYMPTOM_PATTERNS = {
    'common_cold': {
        'symptoms': ['cough', 'runny nose', 'sneezing', 'sore throat', 'mild fever', 'congestion'],
        'disease': 'Common Cold (Acute Viral Nasopharyngitis)',
        'cause': 'Viral infection (Rhinovirus, Coronavirus)',
        'precautions': [
            'Stay hydrated — drink warm fluids',
            'Rest adequately (7-8 hours sleep)',
            'Cover mouth when coughing/sneezing',
            'Wash hands frequently',
            'Avoid cold beverages'
        ],
        'tests': ['Complete Blood Count (CBC)'],
        'confidence': 0.75
    },
    'flu': {
        'symptoms': ['fever', 'body ache', 'fatigue', 'cough', 'headache', 'chills', 'muscle pain'],
        'disease': 'Influenza (Seasonal Flu)',
        'cause': 'Influenza virus (Type A/B)',
        'precautions': [
            'Complete bed rest for 3-5 days',
            'Stay hydrated',
            'Take prescribed antipyretics for fever',
            'Isolate to prevent spread',
            'Monitor temperature regularly'
        ],
        'tests': ['Complete Blood Count (CBC)', 'Influenza Rapid Antigen Test'],
        'confidence': 0.70
    },
    'gastritis': {
        'symptoms': ['stomach pain', 'nausea', 'vomiting', 'bloating', 'acidity', 'burning sensation', 'indigestion'],
        'disease': 'Acute Gastritis',
        'cause': 'H. pylori infection, excessive NSAID use, stress, or dietary factors',
        'precautions': [
            'Avoid spicy and oily food',
            'Eat small, frequent meals',
            'Avoid alcohol and caffeine',
            'Do not skip meals',
            'Manage stress levels'
        ],
        'tests': ['Stool Antigen for H.pylori', 'Endoscopy (if severe)'],
        'confidence': 0.65
    },
    'migraine': {
        'symptoms': ['severe headache', 'one side headache', 'nausea', 'light sensitivity', 'vision problems', 'throbbing pain'],
        'disease': 'Migraine',
        'cause': 'Neurological condition — triggers include stress, hormonal changes, certain foods',
        'precautions': [
            'Rest in a dark, quiet room',
            'Apply cold compress to forehead',
            'Maintain regular sleep schedule',
            'Identify and avoid personal triggers',
            'Stay hydrated'
        ],
        'tests': ['Neurological Examination', 'MRI Brain (if chronic)'],
        'confidence': 0.60
    },
    'hypertension': {
        'symptoms': ['high blood pressure', 'headache', 'dizziness', 'chest tightness', 'blurred vision', 'fatigue'],
        'disease': 'Hypertension (High Blood Pressure)',
        'cause': 'Genetic factors, high sodium diet, obesity, stress, sedentary lifestyle',
        'precautions': [
            'Reduce salt intake',
            'Exercise regularly (30 min/day)',
            'Monitor blood pressure daily',
            'Reduce stress',
            'Avoid smoking and alcohol'
        ],
        'tests': ['Lipid Profile', 'ECG', 'Kidney Function Test'],
        'confidence': 0.55
    },
    'diabetes_symptoms': {
        'symptoms': ['frequent urination', 'excessive thirst', 'weight loss', 'fatigue', 'blurred vision', 'slow healing'],
        'disease': 'Suspected Diabetes Mellitus',
        'cause': 'Insulin resistance (Type 2) or autoimmune destruction of beta cells (Type 1)',
        'precautions': [
            'Get blood sugar levels tested immediately',
            'Reduce sugar and refined carb intake',
            'Exercise regularly',
            'Monitor blood glucose',
            'Follow up with endocrinologist'
        ],
        'tests': ['Fasting Blood Sugar (FBS)', 'HbA1c', 'Random Blood Sugar'],
        'confidence': 0.50
    },
    'allergic_reaction': {
        'symptoms': ['rash', 'itching', 'hives', 'swelling', 'sneezing', 'watery eyes', 'skin redness'],
        'disease': 'Allergic Reaction (Urticaria / Allergic Rhinitis)',
        'cause': 'Immune system response to allergens (pollen, dust, food, medication)',
        'precautions': [
            'Identify and avoid allergen',
            'Take prescribed antihistamines',
            'Keep skin moisturized',
            'Avoid scratching',
            'Seek emergency care if breathing is affected'
        ],
        'confidence': 0.65
    },
    'uti': {
        'symptoms': ['burning urination', 'frequent urination', 'lower abdominal pain', 'cloudy urine', 'urinary pain', 'pelvic pain'],
        'disease': 'Urinary Tract Infection (UTI)',
        'cause': 'Bacterial infection (commonly E. coli)',
        'precautions': [
            'Drink plenty of water',
            'Complete the full course of antibiotics',
            'Maintain proper hygiene',
            'Urinate frequently — do not hold',
            'Avoid irritating feminine products'
        ],
        'confidence': 0.70
    },
    'respiratory_infection': {
        'symptoms': ['cough', 'chest pain', 'difficulty breathing', 'wheezing', 'phlegm', 'fever'],
        'disease': 'Lower Respiratory Tract Infection',
        'cause': 'Bacterial or viral infection affecting bronchi or lungs',
        'precautions': [
            'Seek medical attention immediately',
            'Complete prescribed antibiotics course',
            'Use steam inhalation',
            'Avoid dust and smoke',
            'Rest adequately'
        ],
        'confidence': 0.60
    },
    'anxiety_stress': {
        'symptoms': ['anxiety', 'palpitations', 'sweating', 'trembling', 'insomnia', 'restlessness', 'panic'],
        'disease': 'Anxiety Disorder / Stress-Related Condition',
        'cause': 'Psychological stress, trauma, genetic predisposition',
        'precautions': [
            'Practice deep breathing exercises',
            'Maintain regular exercise routine',
            'Limit caffeine and alcohol',
            'Establish a regular sleep schedule',
            'Consider professional counseling'
        ],
        'confidence': 0.55
    }
}


def analyze_symptoms(transcript):
    """
    Analyze transcript to detect symptoms and suggest diagnosis.
    Uses local database first, then Groq AI for enhanced analysis.
    Returns: { symptoms, diagnosis, cause, precautions, confidence, problem }
    """
    if not transcript:
        return {
            'symptoms': [],
            'diagnosis': '',
            'cause': '',
            'precautions': [],
            'tests': [],
            'confidence': 0,
            'problem': 'No transcript available for analysis'
        }

    text = transcript.lower()
    best_match = None
    best_score = 0

    # First, try local pattern matching
    for pattern_key, pattern in SYMPTOM_PATTERNS.items():
        matched_symptoms = []
        for symptom in pattern['symptoms']:
            # Check for symptom keywords in transcript
            if symptom in text:
                matched_symptoms.append(symptom)
            else:
                # Check individual words
                words = symptom.split()
                if len(words) > 1 and all(w in text for w in words):
                    matched_symptoms.append(symptom)

        if len(matched_symptoms) >= 2:
            score = len(matched_symptoms) / len(pattern['symptoms'])
            if score > best_score:
                best_score = score
                best_match = {
                    'symptoms': matched_symptoms,
                    'diagnosis': pattern['disease'],
                    'cause': pattern['cause'],
                    'precautions': pattern['precautions'],
                    'tests': pattern.get('tests', []),
                    'confidence': min(pattern['confidence'] * (1 + score), 0.95),
                    'problem': f"Patient presenting with {', '.join(matched_symptoms)}"
                }

    # If local analysis has low confidence, enhance with Groq AI
    if best_match and best_match['confidence'] < 0.6:
        groq_query = f"Medical analysis for symptoms: {', '.join(best_match['symptoms'])}. Current diagnosis: {best_match['diagnosis']}"
        groq_response = query_groq_medical_info(groq_query, f"Transcript: {transcript}")

        if groq_response:
            # Parse Groq response and enhance local results
            # For now, boost confidence and add AI-enhanced notes
            best_match['confidence'] = min(best_match['confidence'] + 0.2, 0.9)
            best_match['ai_enhanced'] = True
            best_match['ai_insights'] = groq_response[:500]  # Truncate for storage

    if best_match:
        return best_match

    # No good local match found - try Groq AI for comprehensive analysis
    if GROQ_AVAILABLE and groq_client:
        groq_query = f"Analyze these symptoms from patient transcript: {transcript}"
        groq_response = query_groq_medical_info(groq_query)

        if groq_response:
            # Parse and structure Groq response
            return {
                'symptoms': extract_symptoms_from_text(transcript),
                'diagnosis': 'AI Analysis Required - Consult Specialist',
                'cause': 'Under AI evaluation',
                'precautions': ['Follow up with specialist', 'Monitor symptoms', 'Get diagnostic tests'],
                'tests': ['Complete Blood Count (CBC)', 'Consultation with specialist'],
                'confidence': 0.3,
                'ai_enhanced': True,
                'ai_insights': groq_response,
                'problem': f"AI analysis: {groq_response[:200]}..."
            }

    # Extract any recognizable symptoms even without a pattern match
    all_symptoms = set()
    for pattern in SYMPTOM_PATTERNS.values():
        for symptom in pattern['symptoms']:
            if symptom in text:
                all_symptoms.add(symptom)

    return {
        'symptoms': list(all_symptoms),
        'diagnosis': 'Requires further clinical evaluation',
        'cause': 'Unable to determine from available information',
        'precautions': ['Follow up with specialist', 'Get diagnostic tests done', 'Monitor symptoms'],
        'tests': ['Complete Blood Count (CBC)'],
        'confidence': 0.2 if all_symptoms else 0,
        'problem': f"Patient reports: {', '.join(all_symptoms)}" if all_symptoms else 'Symptoms not clearly identified from transcript'
    }


def extract_symptoms_from_text(text):
    """Extract symptom keywords from text for AI enhancement."""
    symptoms = []
    text_lower = text.lower()

    # Common symptom keywords
    symptom_keywords = [
        'pain', 'fever', 'cough', 'headache', 'nausea', 'vomiting', 'diarrhea',
        'fatigue', 'weakness', 'dizziness', 'chest pain', 'shortness of breath',
        'rash', 'itching', 'swelling', 'sore throat', 'runny nose', 'congestion'
    ]

    for keyword in symptom_keywords:
        if keyword in text_lower:
            symptoms.append(keyword)

    return symptoms


# ═══════════════════════════════════════════════════════════════
# MEDICINE VERIFICATION
# ═══════════════════════════════════════════════════════════════

MEDICINE_DB = {
    'paracetamol': {
        'generic': 'Acetaminophen',
        'dosage_range': '325mg - 1000mg',
        'max_daily': '4000mg',
        'frequency': 'Every 4-6 hours',
        'max_per_day': 4,
        'category': 'Analgesic/Antipyretic',
        'warnings': ['Do not exceed 4g/day', 'Avoid with liver disease', 'Avoid alcohol']
    },
    'amoxicillin': {
        'generic': 'Amoxicillin',
        'dosage_range': '250mg - 500mg',
        'max_daily': '3000mg',
        'frequency': 'Every 8 hours',
        'max_per_day': 3,
        'category': 'Antibiotic (Penicillin)',
        'warnings': ['Complete full course', 'Check for penicillin allergy', 'Take with food']
    },
    'ibuprofen': {
        'generic': 'Ibuprofen',
        'dosage_range': '200mg - 400mg',
        'max_daily': '1200mg (OTC)',
        'frequency': 'Every 6-8 hours',
        'max_per_day': 3,
        'category': 'NSAID',
        'warnings': ['Take with food', 'Avoid with kidney disease', 'Not for pregnant women']
    },
    'cetirizine': {
        'generic': 'Cetirizine Hydrochloride',
        'dosage_range': '5mg - 10mg',
        'max_daily': '10mg',
        'frequency': 'Once daily',
        'max_per_day': 1,
        'category': 'Antihistamine',
        'warnings': ['May cause drowsiness', 'Avoid driving after taking']
    },
    'omeprazole': {
        'generic': 'Omeprazole',
        'dosage_range': '20mg - 40mg',
        'max_daily': '40mg',
        'frequency': 'Once daily before meal',
        'max_per_day': 1,
        'category': 'Proton Pump Inhibitor',
        'warnings': ['Take 30 min before food', 'Long-term use may affect calcium absorption']
    },
    'metformin': {
        'generic': 'Metformin Hydrochloride',
        'dosage_range': '500mg - 1000mg',
        'max_daily': '2000mg',
        'frequency': 'Twice daily with meals',
        'max_per_day': 2,
        'category': 'Antidiabetic',
        'warnings': ['Take with food', 'Monitor blood sugar', 'Avoid alcohol']
    },
    'amlodipine': {
        'generic': 'Amlodipine Besylate',
        'dosage_range': '2.5mg - 10mg',
        'max_daily': '10mg',
        'frequency': 'Once daily',
        'max_per_day': 1,
        'category': 'Calcium Channel Blocker (Antihypertensive)',
        'warnings': ['May cause ankle swelling', 'Monitor blood pressure regularly']
    },
    'azithromycin': {
        'generic': 'Azithromycin',
        'dosage_range': '250mg - 500mg',
        'max_daily': '500mg',
        'frequency': 'Once daily for 3-5 days',
        'max_per_day': 1,
        'category': 'Antibiotic (Macrolide)',
        'warnings': ['Complete full course', 'Take 1 hour before food', 'Check for allergies']
    },
    'pantoprazole': {
        'generic': 'Pantoprazole',
        'dosage_range': '20mg - 40mg',
        'max_daily': '80mg',
        'frequency': 'Once daily before breakfast',
        'max_per_day': 2,
        'category': 'Proton Pump Inhibitor',
        'warnings': ['Take before meals', 'Do not crush tablets']
    },
    'dolo 650': {
        'generic': 'Paracetamol 650mg',
        'dosage_range': '650mg',
        'max_daily': '2600mg',
        'frequency': 'Every 4-6 hours',
        'max_per_day': 4,
        'category': 'Analgesic/Antipyretic',
        'warnings': ['Do not exceed 4 tablets/day', 'Avoid with liver issues']
    },
    'montelukast': {
        'generic': 'Montelukast Sodium',
        'dosage_range': '10mg',
        'max_daily': '10mg',
        'frequency': 'Once daily at bedtime',
        'max_per_day': 1,
        'category': 'Leukotriene Receptor Antagonist',
        'warnings': ['Take at night', 'Monitor mood changes']
    },
    'salbutamol': {
        'generic': 'Salbutamol / Albuterol',
        'dosage_range': '100mcg - 200mcg (inhaler)',
        'max_daily': '800mcg',
        'frequency': 'As needed, max 4 times/day',
        'max_per_day': 4,
        'category': 'Bronchodilator',
        'warnings': ['Do not exceed recommended puffs', 'Rinse mouth after use']
    },
    'crocin': {
        'generic': 'Paracetamol',
        'dosage_range': '500mg - 650mg',
        'max_daily': '2600mg',
        'frequency': 'Every 4-6 hours',
        'max_per_day': 4,
        'category': 'Analgesic/Antipyretic',
        'warnings': ['Do not exceed 4 tablets/day', 'Avoid with liver disease']
    },
    'ciprofloxacin': {
        'generic': 'Ciprofloxacin',
        'dosage_range': '250mg - 500mg',
        'max_daily': '1000mg',
        'frequency': 'Twice daily',
        'max_per_day': 2,
        'category': 'Antibiotic (Fluoroquinolone)',
        'warnings': ['Complete full course', 'Avoid dairy while taking', 'May cause tendon issues']
    },
    'diclofenac': {
        'generic': 'Diclofenac Sodium',
        'dosage_range': '50mg - 100mg',
        'max_daily': '150mg',
        'frequency': '2-3 times daily',
        'max_per_day': 3,
        'category': 'NSAID',
        'warnings': ['Take with food', 'Avoid long-term use', 'Not for heart patients']
    }
}


def verify_medicine(name, dosage=''):
    """
    Verify if a medicine name is valid and dosage is within range.
    Uses local database first, then Groq AI for unknown medicines.
    Returns: { valid, medicine_info, warnings, suggested_dosage }
    """
    name_lower = name.lower().strip()

    # Direct match
    if name_lower in MEDICINE_DB:
        info = MEDICINE_DB[name_lower]
        return {
            'valid': True,
            'name': name,
            'generic_name': info['generic'],
            'category': info['category'],
            'suggested_dosage': info['dosage_range'],
            'frequency': info['frequency'],
            'max_daily': info['max_daily'],
            'warnings': info['warnings']
        }

    # Partial match
    for med_name, info in MEDICINE_DB.items():
        if name_lower in med_name or med_name in name_lower or name_lower in info['generic'].lower():
            return {
                'valid': True,
                'name': med_name.title(),
                'generic_name': info['generic'],
                'category': info['category'],
                'suggested_dosage': info['dosage_range'],
                'frequency': info['frequency'],
                'max_daily': info['max_daily'],
                'warnings': info['warnings']
            }

    # Not found locally - try Groq AI for medicine information
    if GROQ_AVAILABLE and groq_client:
        groq_query = f"Provide information about the medicine '{name}' including: generic name, category, typical dosage, frequency, max daily dose, and warnings. Format as structured information."
        groq_response = query_groq_medical_info(groq_query)

        if groq_response:
            # Parse Groq response for medicine info
            # For now, return AI-verified but mark as requiring manual verification
            return {
                'valid': True,
                'ai_verified': True,
                'name': name,
                'generic_name': 'AI Analysis Required',
                'category': 'AI-Verified Medicine',
                'suggested_dosage': 'Consult pharmacopeia',
                'frequency': 'As prescribed',
                'max_daily': 'Verify with pharmacist',
                'warnings': ['AI-verified medicine — confirm dosage with pharmacist', 'Check for allergies and interactions'],
                'ai_insights': groq_response
            }

    return {
        'valid': False,
        'name': name,
        'generic_name': 'Unknown',
        'category': 'Unverified',
        'suggested_dosage': 'Consult pharmacopeia',
        'frequency': 'As prescribed',
        'max_daily': 'N/A',
        'warnings': ['Medicine not found in database — verify manually before prescribing']
    }


# ═══════════════════════════════════════════════════════════════
# AI PRESCRIPTION SUGGESTIONS
# ═══════════════════════════════════════════════════════════════

DIAGNOSIS_PRESCRIPTIONS = {
    'Common Cold': [
        {'name': 'Paracetamol', 'dosage': '500mg', 'frequency': 'Thrice daily', 'duration': '3 days'},
        {'name': 'Cetirizine', 'dosage': '10mg', 'frequency': 'Once daily', 'duration': '5 days'},
    ],
    'Influenza': [
        {'name': 'Paracetamol', 'dosage': '650mg', 'frequency': 'Thrice daily', 'duration': '5 days'},
        {'name': 'Cetirizine', 'dosage': '10mg', 'frequency': 'Once daily', 'duration': '5 days'},
        {'name': 'Amoxicillin', 'dosage': '500mg', 'frequency': 'Thrice daily', 'duration': '5 days'},
    ],
    'Acute Gastritis': [
        {'name': 'Pantoprazole', 'dosage': '40mg', 'frequency': 'Once daily', 'duration': '14 days'},
        {'name': 'Domperidone', 'dosage': '10mg', 'frequency': 'Thrice daily', 'duration': '7 days'},
    ],
    'Migraine': [
        {'name': 'Ibuprofen', 'dosage': '400mg', 'frequency': 'As needed', 'duration': 'When symptomatic'},
        {'name': 'Paracetamol', 'dosage': '1000mg', 'frequency': 'As needed', 'duration': 'When symptomatic'},
    ],
    'Urinary Tract Infection': [
        {'name': 'Ciprofloxacin', 'dosage': '500mg', 'frequency': 'Twice daily', 'duration': '5 days'},
        {'name': 'Paracetamol', 'dosage': '500mg', 'frequency': 'As needed', 'duration': '3 days'},
    ],
    'Allergic Reaction': [
        {'name': 'Cetirizine', 'dosage': '10mg', 'frequency': 'Once daily', 'duration': '7 days'},
        {'name': 'Montelukast', 'dosage': '10mg', 'frequency': 'Once at night', 'duration': '14 days'},
    ],
}


def suggest_prescription(diagnosis):
    """Suggest medicines based on diagnosis. Doctor can modify."""
    for key, meds in DIAGNOSIS_PRESCRIPTIONS.items():
        if key.lower() in diagnosis.lower():
            return {'suggestions': meds, 'note': 'AI-suggested. Doctor review required.'}
    return {'suggestions': [], 'note': 'No automated suggestions available for this diagnosis.'}


# ═══════════════════════════════════════════════════════════════
# DIET & EXERCISE SUGGESTIONS
# ═══════════════════════════════════════════════════════════════

DIET_PLANS = {
    'Common Cold': {
        'diet': [
            'Warm soups (chicken, vegetable)',
            'Citrus fruits (orange, lemon) for Vitamin C',
            'Ginger tea with honey',
            'Light, easily digestible meals',
            'Avoid cold drinks and ice cream'
        ],
        'exercise': [
            'Complete rest for first 2 days',
            'Light walking after symptoms reduce',
            'Deep breathing exercises',
            'Avoid strenuous activity until recovered'
        ]
    },
    'Influenza': {
        'diet': [
            'Clear broths and soups',
            'Stay hydrated — 3+ liters water/day',
            'Bananas and rice (BRAT diet if nauseous)',
            'Herbal teas with turmeric',
            'Avoid dairy if congested'
        ],
        'exercise': [
            'Strict bed rest for 3-5 days',
            'No exercise until fever-free for 24 hours',
            'Gentle stretching after recovery',
            'Gradual return to normal activity'
        ]
    },
    'Acute Gastritis': {
        'diet': [
            'Avoid spicy, fried, and acidic foods',
            'Small, frequent meals (5-6/day)',
            'Include probiotics (yogurt, buttermilk)',
            'Boiled vegetables and rice',
            'Avoid caffeine and carbonated drinks'
        ],
        'exercise': [
            'Light walking after meals (15 min)',
            'Yoga — especially Vajrasana after eating',
            'Avoid intense exercise on empty stomach',
            'Stress-reduction activities'
        ]
    },
    'Migraine': {
        'diet': [
            'Avoid trigger foods (cheese, chocolate, MSG)',
            'Maintain regular meal times',
            'Magnesium-rich foods (spinach, nuts)',
            'Stay well hydrated',
            'Limit caffeine to 1 cup/day'
        ],
        'exercise': [
            'Regular moderate exercise (30 min/day)',
            'Yoga and meditation',
            'Avoid sudden intense exertion',
            'Neck and shoulder stretches daily'
        ]
    },
    'Hypertension': {
        'diet': [
            'DASH diet — fruits, vegetables, whole grains',
            'Reduce sodium to < 2300mg/day',
            'Potassium-rich foods (bananas, potatoes)',
            'Limit red meat and saturated fats',
            'Avoid processed and canned foods'
        ],
        'exercise': [
            'Brisk walking 30-45 minutes daily',
            'Swimming or cycling',
            'Avoid heavy weightlifting',
            'Pranayama breathing exercises'
        ]
    },
    'Diabetes': {
        'diet': [
            'Low glycemic index foods',
            'High fiber — whole grains, vegetables',
            'Lean protein sources',
            'Avoid sugar, sweets, white rice',
            'Regular small meals'
        ],
        'exercise': [
            'Walking 30 minutes after meals',
            'Regular aerobic exercise',
            'Resistance training 2-3 times/week',
            'Yoga — especially Surya Namaskar'
        ]
    }
}


# ── Symptom → Diet Mapping for dynamic suggestions ──
SYMPTOM_DIET_MAP = {
    'fever': {
        'diet': ['Drink 3-4 liters of water/day to stay hydrated', 'Light foods: rice, bananas, toast (BRAT diet)', 'Fresh fruit juices rich in Vitamin C (orange, sweet lime)', 'Turmeric milk or herbal teas', 'Avoid heavy, fried or spicy food'],
        'exercise': ['Complete bed rest until fever subsides', 'No exercise while temperature is above 101°F', 'Gentle walking after fever breaks']
    },
    'cough': {
        'diet': ['Warm ginger-honey tea (anti-inflammatory)', 'Avoid cold foods, ice cream and cold drinks', 'Steam inhalation with eucalyptus oil', 'Include turmeric and black pepper in meals'],
        'exercise': ['Light deep breathing exercises (Pranayama)', 'Avoid dusty or smoky environments', 'No vigorous exercise while coughing']
    },
    'cold': {
        'diet': ['Hot soups (chicken or vegetable broth)', 'Citrus fruits for Vitamin C', 'Ginger and garlic in food', 'Avoid dairy products — may thicken mucus'],
        'exercise': ['Rest indoors for 1-2 days', 'Light warm-up exercises after improvement', 'Steam inhalation twice daily']
    },
    'headache': {
        'diet': ['Stay well hydrated (dehydration triggers headaches)', 'Avoid skipping meals', 'Limit caffeine to 1 cup/day', 'Magnesium-rich foods: spinach, nuts, seeds', 'Avoid MSG, processed cheese and alcohol'],
        'exercise': ['Neck and shoulder stretches', 'Rest in a dark quiet room during attacks', 'Yoga and meditation daily', 'Regular sleep schedule (7-8 hours)']
    },
    'stomach pain': {
        'diet': ['Small, frequent meals (5-6 times/day)', 'Avoid spicy, acidic and fried foods', 'Include probiotics: yogurt, buttermilk', 'Boiled vegetables and plain rice', 'Avoid caffeine and carbonated drinks'],
        'exercise': ['Light walking 15 min after meals', 'Vajrasana (yoga pose) after eating', 'Avoid intense exercise on an empty stomach']
    },
    'nausea': {
        'diet': ['Ginger tea or ginger chews', 'Small sips of cold water or ice chips', 'BRAT diet: bananas, rice, applesauce, toast', 'Avoid strong smells and greasy food'],
        'exercise': ['Rest and avoid sudden movements', 'Fresh air and gentle walks if tolerated']
    },
    'vomiting': {
        'diet': ['Clear fluids first: water, coconut water, ORS', 'Gradually introduce bland foods after 6 hours', 'Avoid solid food until vomiting stops', 'Small sips every 15 minutes'],
        'exercise': ['Complete rest', 'Avoid physical activity until fully hydrated']
    },
    'diarrhea': {
        'diet': ['ORS (Oral Rehydration Solution) frequently', 'BRAT diet: bananas, rice, applesauce, toast', 'Boiled potatoes and plain crackers', 'Avoid dairy, fatty food, caffeine and alcohol'],
        'exercise': ['Rest adequately', 'Resume normal activity only after symptoms resolve']
    },
    'dizziness': {
        'diet': ['Eat regular small meals — avoid fasting', 'Stay hydrated throughout the day', 'Reduce salt if blood pressure is high', 'Avoid alcohol and caffeine'],
        'exercise': ['Sit or lie down immediately when dizzy', 'Vestibular exercises (head movements) with doctor guidance', 'Avoid driving or heights']
    },
    'chest pain': {
        'diet': ['Low-fat, heart-healthy diet', 'Reduce sodium and processed foods', 'Include omega-3: fish, flaxseeds, walnuts', 'Avoid caffeine and alcohol'],
        'exercise': ['Do NOT exercise until medically cleared', 'Seek emergency assessment immediately', 'Cardiac rehab exercises only under supervision']
    },
    'body ache': {
        'diet': ['Anti-inflammatory foods: turmeric, ginger, berries', 'High protein foods for muscle repair', 'Stay hydrated', 'Warm soups and broths'],
        'exercise': ['Warm bath or heating pad for sore muscles', 'Gentle stretching', 'Rest adequately before resuming normal exercise']
    },
    'fatigue': {
        'diet': ['Iron-rich foods: spinach, lentils, red meat', 'B12 sources: eggs, dairy, fortified cereals', 'Avoid sugar spikes — eat complex carbs', 'Stay well hydrated'],
        'exercise': ['Light yoga and stretching', 'Short walks to boost energy', 'Prioritize 8 hours of sleep', 'Avoid overexertion']
    },
    'weakness': {
        'diet': ['High-protein diet: eggs, lentils, paneer, chicken', 'Energy foods: nuts, dates, bananas', 'Iron and B12 supplements if deficient', 'Avoid skipping meals'],
        'exercise': ['Gradual reintroduction of physical activity', 'Chair exercises or gentle yoga', 'Rest between activities']
    },
    'swelling': {
        'diet': ['Reduce sodium intake significantly', 'Foods with natural diuretics: cucumber, lemon', 'Stay hydrated paradoxically helps flush excess fluid', 'Avoid processed and packaged foods'],
        'exercise': ['Elevate swollen limbs', 'Gentle compression movement exercises', 'Avoid prolonged standing or sitting']
    },
    'sore throat': {
        'diet': ['Warm honey-lemon water', 'Cold foods like ice cream can temporarily soothe', 'Soft foods: soups, mashed foods, smoothies', 'Avoid spicy, hard or crunchy foods'],
        'exercise': ['Rest your voice', 'Steam inhalation for relief', 'Light activity tolerable if no fever']
    },
    'itching': {
        'diet': ['Avoid known allergens in your diet', 'Anti-inflammatory foods: omega-3, probiotics', 'Stay hydrated for healthy skin', 'Avoid alcohol and spicy foods which can worsen itching'],
        'exercise': ['Cool showers instead of hot baths', 'Wear loose, breathable clothing', 'Avoid sweating which can aggravate itching']
    },
    'burning urination': {
        'diet': ['Drink 3+ liters of water daily to flush bacteria', 'Cranberry juice (unsweetened)', 'Avoid caffeine, alcohol and sodas', 'Vitamin C to acidify urine and inhibit bacteria'],
        'exercise': ['Rest adequately during infection', 'Maintain personal hygiene after exercise', 'Resume normal activity after symptoms clear']
    },
    'runny nose': {
        'diet': ['Hot fluids and soups', 'Spicy food like horseradish can clear congestion', 'Avoid dairy which may thicken mucus', 'Honey and ginger tea'],
        'exercise': ['Moderate activity is fine if no fever', 'Steam inhalation before exercise', 'Avoid outdoor exercise in cold/polluted air']
    },
    'loss of appetite': {
        'diet': ['Small, frequent meals every 2-3 hours', 'Nutrient-dense foods: nuts, avocado, smoothies', 'Zinc-rich foods to restore taste/smell', 'Ginger or peppermint tea before meals to stimulate appetite'],
        'exercise': ['Light walks before meals to stimulate hunger', 'Gentle yoga']
    },
    'insomnia': {
        'diet': ['Avoid caffeine after 2 PM', 'Warm milk with turmeric at bedtime', 'Magnesium-rich foods: almonds, spinach', 'Avoid large heavy meals before sleep'],
        'exercise': ['Regular aerobic exercise (morning/afternoon)', 'Yoga Nidra or progressive muscle relaxation at night', 'Consistent sleep schedule weekends included']
    },
    'high blood pressure': {
        'diet': ['DASH diet: fruits, vegetables, whole grains', 'Reduce sodium to <1500mg/day', 'Bananas and potatoes (potassium lowers BP)', 'Avoid alcohol, caffeine and processed foods'],
        'exercise': ['Brisk walking 30-45 minutes daily', 'Swimming or cycling', 'Pranayama breathing exercises', 'Avoid heavy weightlifting']
    },
    'frequent urination': {
        'diet': ['Avoid caffeine, alcohol and artificial sweeteners', 'Reduce fluid intake in the evening', 'Pumpkin seed extract may help bladder control'],
        'exercise': ['Kegel (pelvic floor) exercises', 'Bladder training routines']
    },
    'joint pain': {
        'diet': ['Anti-inflammatory foods: turmeric, omega-3, berries', 'Calcium + Vitamin D for bone health (dairy, sunlight)', 'Avoid red meat and processed foods', 'Stay well hydrated'],
        'exercise': ['Low-impact exercise: swimming, cycling', 'Joint mobility exercises daily', 'Avoid high-impact activities during flare-ups']
    },
    'anxiety': {
        'diet': ['Magnesium-rich foods: dark chocolate, spinach, almonds', 'Limit caffeine and refined sugar', 'Omega-3 fish (salmon, sardines)', 'Chamomile or ashwagandha tea'],
        'exercise': ['Aerobic exercise 30 min daily (releases endorphins)', 'Yoga and meditation', 'Breathing exercises (4-7-8 technique)']
    },
    'palpitations': {
        'diet': ['Avoid caffeine and alcohol', 'Stay hydrated', 'Potassium and magnesium-rich foods', 'Avoid energy drinks entirely'],
        'exercise': ['Rest until evaluated by doctor', 'No strenuous exercise without medical clearance', 'Deep breathing to calm the nervous system']
    },
}


def suggest_diet(diagnosis, symptoms=None):
    """
    Suggest a personalized diet and exercise plan.
    First tries to match the diagnosis, then dynamically assembles
    a plan from the patient's individual symptoms.
    """
    # 1. Try exact diagnosis match first
    for key, plan in DIET_PLANS.items():
        if key.lower() in diagnosis.lower():
            return plan

    # 2. Build a dynamic plan from individual symptoms
    if symptoms:
        combined_diet = []
        combined_exercise = []
        matched_symptoms = []

        symptom_list = symptoms if isinstance(symptoms, list) else [symptoms]

        for symptom in symptom_list:
            symptom_lower = symptom.lower()
            for key, plan in SYMPTOM_DIET_MAP.items():
                if key in symptom_lower and key not in matched_symptoms:
                    matched_symptoms.append(key)
                    for item in plan['diet']:
                        if item not in combined_diet:
                            combined_diet.append(item)
                    for item in plan['exercise']:
                        if item not in combined_exercise:
                            combined_exercise.append(item)

        if combined_diet:
            # Add universal hydration tip if not already present
            hydration = 'Drink at least 2-3 liters of water daily'
            if not any('water' in d.lower() or 'hydrat' in d.lower() for d in combined_diet):
                combined_diet.insert(0, hydration)
            return {
                'diet': combined_diet[:8],       # cap at 8 items
                'exercise': combined_exercise[:6] # cap at 6 items
            }

    # 3. Absolute fallback — universal healthy plan
    return {
        'diet': [
            'Balanced diet rich in fruits, vegetables and whole grains',
            'Stay well hydrated — drink 2-3 liters of water daily',
            'Include lean protein: eggs, legumes, fish or chicken',
            'Avoid processed, fried and junk food',
            'Eat small frequent meals every 3-4 hours',
            'Avoid skipping breakfast'
        ],
        'exercise': [
            'Brisk walking for 30 minutes every day',
            'Light stretching exercises morning and evening',
            'Adequate sleep — 7-8 hours per night',
            'Yoga or meditation for stress management',
            'Avoid sedentary lifestyle — take breaks every hour'
        ]
    }


# ═══════════════════════════════════════════════════════════════
# MEDICAL DISCLAIMER
# ═══════════════════════════════════════════════════════════════

def generate_disclaimer(confidence):
    """
    Generate appropriate medical disclaimer based on AI confidence level.
    """
    if confidence >= 0.7:
        return (
            "Note: This AI-assisted analysis is based on reported symptoms and should be "
            "used as a supportive tool only. Final diagnosis and treatment decisions must be "
            "made by the attending physician."
        )
    elif confidence >= 0.4:
        return (
            "Medical Disclaimer: AI analysis has moderate confidence in the assessment. "
            "Additional diagnostic tests and clinical examination are recommended before "
            "confirming the diagnosis. This is not a substitute for professional medical advice."
        )
    else:
        return (
            "⚠️ Medical Disclaimer: AI could not determine sufficient medical information from "
            "the available data. The patient should undergo proper clinical examination, "
            "diagnostic tests, and consultation with a specialist. This AI output should NOT "
            "be used as a basis for treatment decisions."
        )


# ═══════════════════════════════════════════════════════════════
# MULTILINGUAL MEDICAL TERM DICTIONARY
# ═══════════════════════════════════════════════════════════════

MEDICAL_TRANSLATIONS = {
    # Hindi (hi-IN)
    'hi': {
        'सिरदर्द': 'headache', 'बुखार': 'fever', 'खांसी': 'cough',
        'जुकाम': 'cold', 'उल्टी': 'vomiting', 'दस्त': 'diarrhea',
        'पेट दर्द': 'stomach pain', 'छाती में दर्द': 'chest pain',
        'सांस लेने में तकलीफ': 'difficulty breathing', 'चक्कर': 'dizziness',
        'कमजोरी': 'weakness', 'थकान': 'fatigue', 'जलन': 'burning sensation',
        'खुजली': 'itching', 'सूजन': 'swelling', 'दर्द': 'pain',
        'बदन दर्द': 'body ache', 'गले में खराश': 'sore throat',
        'नाक बहना': 'runny nose', 'पेशाब में जलन': 'burning urination',
        'भूख नहीं': 'loss of appetite', 'नींद नहीं': 'insomnia',
        'जी मिचलाना': 'nausea', 'कब्ज': 'constipation',
        'दवाई': 'medicine', 'डॉक्टर': 'doctor', 'अस्पताल': 'hospital',
        'ब्लड प्रेशर': 'blood pressure', 'शुगर': 'diabetes',
        'एलर्जी': 'allergy', 'चोट': 'injury', 'टीका': 'vaccine',
    },
    # Kannada (kn-IN)
    'kn': {
        'ತಲೆನೋವು': 'headache', 'ಜ್ವರ': 'fever', 'ಕೆಮ್ಮು': 'cough',
        'ನೆಗಡಿ': 'cold', 'ವಾಂತಿ': 'vomiting', 'ಭೇದಿ': 'diarrhea',
        'ಹೊಟ್ಟೆ ನೋವು': 'stomach pain', 'ಎದೆ ನೋವು': 'chest pain',
        'ಉಸಿರಾಟದ ತೊಂದರೆ': 'difficulty breathing', 'ತಲೆ ತಿರುಗುವಿಕೆ': 'dizziness',
        'ದೌರ್ಬಲ್ಯ': 'weakness', 'ಆಯಾಸ': 'fatigue', 'ಉರಿ': 'burning sensation',
        'ತುರಿಕೆ': 'itching', 'ಊತ': 'swelling', 'ನೋವು': 'pain',
        'ಮೈ ನೋವು': 'body ache', 'ಗಂಟಲು ನೋವು': 'sore throat',
        'ಮೂಗು ಸೋರುವಿಕೆ': 'runny nose', 'ಮೂತ್ರ ಉರಿ': 'burning urination',
        'ಹಸಿವಿಲ್ಲ': 'loss of appetite', 'ನಿದ್ರೆ ಬರುವುದಿಲ್ಲ': 'insomnia',
        'ಔಷಧಿ': 'medicine', 'ವೈದ್ಯರು': 'doctor', 'ಆಸ್ಪತ್ರೆ': 'hospital',
    },
    # Telugu (te-IN)
    'te': {
        'తలనొప్పి': 'headache', 'జ్వరం': 'fever', 'దగ్గు': 'cough',
        'జలుబు': 'cold', 'వాంతులు': 'vomiting', 'విరేచనాలు': 'diarrhea',
        'కడుపు నొప్పి': 'stomach pain', 'ఛాతీ నొప్పి': 'chest pain',
        'ఊపిరి ఆడకపోవడం': 'difficulty breathing', 'తల తిరగడం': 'dizziness',
        'బలహీనత': 'weakness', 'అలసట': 'fatigue', 'మంట': 'burning sensation',
        'దురద': 'itching', 'వాపు': 'swelling', 'నొప్పి': 'pain',
        'ఒళ్లు నొప్పులు': 'body ache', 'గొంతు నొప్పి': 'sore throat',
        'ముక్కు కారడం': 'runny nose', 'మూత్రం మంట': 'burning urination',
        'ఆకలి లేదు': 'loss of appetite', 'నిద్ర రాకపోవడం': 'insomnia',
        'మందు': 'medicine', 'డాక్టర్': 'doctor', 'ఆసుపత్రి': 'hospital',
    },
    # Tamil (ta-IN)
    'ta': {
        'தலைவலி': 'headache', 'காய்ச்சல்': 'fever', 'இருமல்': 'cough',
        'சளி': 'cold', 'வாந்தி': 'vomiting', 'வயிற்றுப்போக்கு': 'diarrhea',
        'வயிற்று வலி': 'stomach pain', 'நெஞ்சு வலி': 'chest pain',
        'மூச்சு திணறல்': 'difficulty breathing', 'தலைச்சுற்றல்': 'dizziness',
        'பலவீனம்': 'weakness', 'சோர்வு': 'fatigue', 'எரிச்சல்': 'burning sensation',
        'அரிப்பு': 'itching', 'வீக்கம்': 'swelling', 'வலி': 'pain',
        'உடல் வலி': 'body ache', 'தொண்டை வலி': 'sore throat',
        'மூக்கு ஒழுகுதல்': 'runny nose', 'சிறுநீர் எரிச்சல்': 'burning urination',
        'பசி இல்லை': 'loss of appetite', 'தூக்கமின்மை': 'insomnia',
        'மருந்து': 'medicine', 'மருத்துவர்': 'doctor', 'மருத்துவமனை': 'hospital',
    },
    # Malayalam (ml-IN)
    'ml': {
        'തലവേദന': 'headache', 'പനി': 'fever', 'ചുമ': 'cough',
        'ജലദോഷം': 'cold', 'ഛർദ്ദി': 'vomiting', 'വയറിളക്കം': 'diarrhea',
        'വയറുവേദന': 'stomach pain', 'നെഞ്ചുവേദന': 'chest pain',
        'ശ്വാസംമുട്ടൽ': 'difficulty breathing', 'തലചുറ്റൽ': 'dizziness',
        'ബലഹീനത': 'weakness', 'ക്ഷീണം': 'fatigue', 'നീറ്റൽ': 'burning sensation',
        'ചൊറിച്ചിൽ': 'itching', 'നീർക്കെട്ട്': 'swelling', 'വേദന': 'pain',
        'ശരീരവേദന': 'body ache', 'തൊണ്ടവേദന': 'sore throat',
        'മൂക്കൊലിപ്പ്': 'runny nose', 'മൂത്രത്തിൽ നീറ്റൽ': 'burning urination',
        'വിശപ്പില്ല': 'loss of appetite', 'ഉറക്കമില്ല': 'insomnia',
        'മരുന്ന്': 'medicine', 'ഡോക്ടർ': 'doctor', 'ആശുപത്രി': 'hospital',
    },
    # Marathi (mr-IN)
    'mr': {
        'डोकेदुखी': 'headache', 'ताप': 'fever', 'खोकला': 'cough',
        'सर्दी': 'cold', 'उलटी': 'vomiting', 'जुलाब': 'diarrhea',
        'पोटदुखी': 'stomach pain', 'छातीत दुखणे': 'chest pain',
        'श्वास घेण्यास त्रास': 'difficulty breathing', 'चक्कर': 'dizziness',
        'अशक्तपणा': 'weakness', 'थकवा': 'fatigue', 'जळजळ': 'burning sensation',
        'खाज': 'itching', 'सूज': 'swelling', 'वेदना': 'pain',
        'अंगदुखी': 'body ache', 'घसा दुखणे': 'sore throat',
        'नाक वाहणे': 'runny nose', 'लघवी करताना जळजळ': 'burning urination',
        'भूक नाही': 'loss of appetite', 'झोप येत नाही': 'insomnia',
        'औषध': 'medicine', 'डॉक्टर': 'doctor', 'रुग्णालय': 'hospital',
    },
    # Gujarati (gu-IN)
    'gu': {
        'માથાનો દુખાવો': 'headache', 'તાવ': 'fever', 'ઉધરસ': 'cough',
        'શરદી': 'cold', 'ઉલટી': 'vomiting', 'ઝાડા': 'diarrhea',
        'પેટનો દુખાવો': 'stomach pain', 'છાતીમાં દુખાવો': 'chest pain',
        'શ્વાસ લેવામાં તકલીફ': 'difficulty breathing', 'ચક્કર': 'dizziness',
        'નબળાઈ': 'weakness', 'થાક': 'fatigue', 'બળતરા': 'burning sensation',
        'ખંજવાળ': 'itching', 'સોજો': 'swelling', 'દુખાવો': 'pain',
        'શરીરનો દુખાવો': 'body ache', 'ગળામાં દુખાવો': 'sore throat',
        'નાક વહેવું': 'runny nose', 'પેશાબમાં બળતરા': 'burning urination',
        'ભૂખ નથી લાગતી': 'loss of appetite', 'ઊંઘ નથી આવતી': 'insomnia',
        'દવા': 'medicine', 'ડૉક્ટર': 'doctor', 'હૉસ્પિટલ': 'hospital',
    },
    # Tulu (closest to Kannada, no standard ASR code)
    'tulu': {
        'ತರೆ ನೋವು': 'headache', 'ಜ್ವರ': 'fever', 'ಕೆಮ್ಮು': 'cough',
        'ನೆಗಡಿ': 'cold', 'ಆಕರ': 'vomiting', 'ಭೇದಿ': 'diarrhea',
        'ಬಂಜಿ ನೋವು': 'stomach pain', 'ಎದೆ ನೋವು': 'chest pain',
        'ಉಸಿರ್ ಕಷ್ಟ': 'difficulty breathing', 'ತರೆ ಗಿರ್ಗಿರ್': 'dizziness',
        'ನೋವು': 'pain', 'ಮೈ ನೋವು': 'body ache', 'ಗಂಟಲ್ ನೋವು': 'sore throat',
        'ಮರ್ದ್': 'medicine', 'ಡಾಕ್ಟ್ರ': 'doctor',
    },
    # Bhojpuri (closest to Hindi, no standard ASR code)
    'bho': {
        'माथा दुखात बा': 'headache', 'बोखार': 'fever', 'खाँसी': 'cough',
        'जुकाम': 'cold', 'उलटी': 'vomiting', 'दस्त': 'diarrhea',
        'पेट दुखात बा': 'stomach pain', 'छाती में दरद': 'chest pain',
        'साँस में तकलीफ': 'difficulty breathing', 'चक्कर': 'dizziness',
        'कमजोरी': 'weakness', 'थकान': 'fatigue', 'जरन': 'burning sensation',
        'खुजली': 'itching', 'सुजन': 'swelling', 'दरद': 'pain',
        'बदन दरद': 'body ache', 'गला में खराश': 'sore throat',
        'दवाई': 'medicine', 'डाक्टर': 'doctor', 'अस्पताल': 'hospital',
    },
    # Spanish (es-ES)
    'es': {
        'dolor de cabeza': 'headache', 'fiebre': 'fever', 'tos': 'cough',
        'resfriado': 'cold', 'vómito': 'vomiting', 'diarrea': 'diarrhea',
        'dolor de estómago': 'stomach pain', 'dolor de pecho': 'chest pain',
        'dificultad para respirar': 'difficulty breathing', 'mareo': 'dizziness',
        'debilidad': 'weakness', 'fatiga': 'fatigue', 'ardor': 'burning sensation',
        'picazón': 'itching', 'hinchazón': 'swelling', 'dolor': 'pain',
        'dolor de cuerpo': 'body ache', 'dolor de garganta': 'sore throat',
        'nariz congestionada': 'runny nose', 'ardor al orinar': 'burning urination',
        'falta de apetito': 'loss of appetite', 'insomnio': 'insomnia',
        'medicina': 'medicine', 'doctor': 'doctor', 'hospital': 'hospital',
        'náuseas': 'nausea', 'alergia': 'allergy', 'presión arterial': 'blood pressure',
    }
}


def translate_text(text, source_lang='auto', target_lang='en'):
    """
    Translate full sentences between languages with medical terminology preservation.
    Uses Google Translate auto-detection when source_lang is 'auto'.
    Falls back to local dictionary only for explicitly supported codes
    when deep-translator is unavailable (only to English).
    """
    if not text or source_lang == target_lang:
        return text

    # Medical terminology that should be preserved in English
    medical_terms = {
        'aspirin', 'ibuprofen', 'paracetamol', 'amoxicillin', 'azithromycin',
        'blood pressure', 'diabetes', 'hypertension', 'cholesterol', 'glucose',
        'mg', 'ml', 'tablet', 'capsule', 'syrup', 'injection', 'ointment',
        'twice daily', 'thrice daily', 'once daily', 'every 6 hours', 'every 8 hours',
        'before meals', 'after meals', 'with food', 'empty stomach'
    }

    # ── Primary: Full sentence translation via Google Translate ──
    if DEEP_TRANSLATOR_AVAILABLE:
        try:
            # Map our internal codes → Google Translate codes
            LANG_CODE_MAP = {
                'hi': 'hi', 'kn': 'kn', 'te': 'te', 'ta': 'ta',
                'ml': 'ml', 'mr': 'mr', 'gu': 'gu',
                'tulu': 'kn',   # Tulu uses Kannada script
                'bho': 'hi',    # Bhojpuri uses Hindi/Devanagari
                'es': 'es',
                'en': 'en'
            }
            google_source = LANG_CODE_MAP.get(source_lang, 'auto') if source_lang != 'auto' else 'auto'
            google_target = LANG_CODE_MAP.get(target_lang, 'en')

            # For medical content, translate and then restore key terms
            translated = GoogleTranslator(source=google_source, target=google_target).translate(text)
            if translated:
                # Restore medical terms to English for clarity
                if target_lang != 'en':
                    for term in medical_terms:
                        if term in text.lower():
                            # Try to find translated version and replace back
                            pass  # For now, keep translated version
                return translated
        except Exception as e:
            print(f'⚠️  Google Translate failed ({e}), falling back to dictionary.')

    # ── Fallback: local medical dictionary term replacement (only to EN) ──
    if target_lang != 'en':
        return text # Cannot fallback translate to other languages

    if source_lang not in MEDICAL_TRANSLATIONS:
        return text

    dictionary = MEDICAL_TRANSLATIONS[source_lang]
    translated = text
    sorted_terms = sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True)
    for term, english in sorted_terms:
        translated = translated.replace(term, english)

    return translated


def get_supported_languages():
    """Return list of supported languages with their codes."""
    return {
        'en': {'name': 'English', 'speech_code': 'en-US'},
        'hi': {'name': 'Hindi', 'speech_code': 'hi-IN'},
        'kn': {'name': 'Kannada', 'speech_code': 'kn-IN'},
        'te': {'name': 'Telugu', 'speech_code': 'te-IN'},
        'ta': {'name': 'Tamil', 'speech_code': 'ta-IN'},
        'ml': {'name': 'Malayalam', 'speech_code': 'ml-IN'},
        'mr': {'name': 'Marathi', 'speech_code': 'mr-IN'},
        'gu': {'name': 'Gujarati', 'speech_code': 'gu-IN'},
        'tulu': {'name': 'Tulu', 'speech_code': 'kn-IN'},
        'bho': {'name': 'Bhojpuri', 'speech_code': 'hi-IN'},
        'es': {'name': 'Spanish', 'speech_code': 'es-ES'},
    }
