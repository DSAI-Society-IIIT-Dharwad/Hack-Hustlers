import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# System instruction for the medical AI
SYSTEM_PROMPT = """You are MediBot, an expert AI medical assistant for the MediConsult platform.
You support three languages: English, Hindi (हिंदी), and Kannada (ಕನ್ನಡ).

Rules:
1. Always detect the language the user is writing in and respond strictly in the SAME language.
2. If the user writes in Hindi (Devanagari script), reply fully in Hindi.
3. If the user writes in Kannada (Kannada script), reply fully in Kannada.
4. If the user writes in English, reply in English.
5. You help patients describe symptoms, understand conditions, and prepare for doctor consultations.
6. Extract and summarize key symptoms when present.
7. NEVER diagnose. Always recommend consulting a qualified doctor for proper diagnosis.
8. Be empathetic, concise, and professional.
9. When extracting symptoms, format them clearly.
10. Keep responses concise (under 200 words usually).
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

def get_ai_response(conversation_history: list, user_message: str) -> dict:
    """
    Generate AI response using Gemini.
    conversation_history: list of {'role': 'user'|'model', 'parts': [str]}
    Returns: {'response': str, 'language': str}
    """
    try:
        # Build chat
        chat = model.start_chat(history=conversation_history)
        response = chat.send_message(user_message)
        reply = response.text.strip()

        # Detect rough language
        language = detect_language(user_message)

        return {"response": reply, "language": language, "error": None}
    except Exception as e:
        return {
            "response": "I'm sorry, I encountered an error. Please try again.",
            "language": "en",
            "error": str(e)
        }


def detect_language(text: str) -> str:
    """Simple script-based language detection."""
    for ch in text:
        code = ord(ch)
        if 0x0900 <= code <= 0x097F:   # Devanagari (Hindi)
            return "hi"
        if 0x0C80 <= code <= 0x0CFF:   # Kannada
            return "kn"
    return "en"


def generate_consultation_report(messages: list, patient_name: str, doctor_name: str) -> str:
    """Generate a structured text report from consultation messages using Gemini."""
    try:
        conversation_text = "\n".join([
            f"{'Patient' if m['sender_role'] == 'patient' else 'AI'}: {m['content']}"
            for m in messages
        ])

        prompt = f"""Based on the following medical consultation conversation, generate a structured clinical report in English.

Patient: {patient_name}
Doctor Assigned: {doctor_name}

Conversation:
{conversation_text}

Generate a report with these sections:
1. Chief Complaint
2. Reported Symptoms
3. Symptom Duration & Severity
4. Relevant History Mentioned
5. AI Assessment Summary
6. Recommended Next Steps

Keep it professional and concise."""

        report_model = genai.GenerativeModel("gemini-1.5-flash")
        response = report_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Report generation failed: {str(e)}"


def get_welcome_message(language: str = "en") -> str:
    """Return a welcome message in the selected language."""
    messages = {
        "en": "👋 Hello! I'm MediBot, your AI health assistant. Please describe your symptoms or health concerns, and I'll help you prepare for your doctor consultation.",
        "hi": "👋 नमस्ते! मैं MediBot हूँ, आपका AI स्वास्थ्य सहायक। कृपया अपने लक्षण या स्वास्थ्य संबंधी चिंताएँ बताएं, और मैं आपकी डॉक्टर परामर्श के लिए तैयारी में मदद करूँगा।",
        "kn": "👋 ನಮಸ್ಕಾರ! ನಾನು MediBot, ನಿಮ್ಮ AI ಆರೋಗ್ಯ ಸಹಾಯಕ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳು ಅಥವಾ ಆರೋಗ್ಯ ಸಮಸ್ಯೆಗಳನ್ನು ವಿವರಿಸಿ, ನಾನು ನಿಮ್ಮ ವೈದ್ಯರ ಸಮಾಲೋಚನೆಗಾಗಿ ತಯಾರಾಗಲು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ."
    }
    return messages.get(language, messages["en"])
