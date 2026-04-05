# MediConsult — AI-Powered Multilingual Telemedicine Platform

A comprehensive telemedicine platform featuring AI-driven medical analysis, real-time multilingual consultations, automated prescription translation, and advanced healthcare management..

## 🚀 Features

### 🤖 AI-Powered Medical Analysis and that
- **Symptom Analysis**: AI analyzes patient symptoms using local database + external APIs (Groq AI, Google Gemini)
- **Urgency Detection**: Automatically detects medical emergencies and prioritizes consultations
- **Medicine Verification**: Validates medicines with comprehensive database and AI assistance
- **Diet & Exercise Recommendations**: Personalized health recommendations
- **Medical Report Generation**: Structured AI-generated consultation reports

### 🌐 Enhanced Multilingual Support
- **15+ Languages**: Hindi, Kannada, Telugu, Tamil, Malayalam, Marathi, Gujarati, Spanish, French, German, etc.
- **Real-time Translation**: Live conversation translation during consultations
- **Prescription Translation**: Automatic translation of prescriptions to patient's native language
- **Medical Terminology**: Preserves medical terms in English for accuracy
- **Language Preference**: User-selectable language settings

### 💊 Smart Prescription System
- **AI-Generated Prescriptions**: Doctor assistance with AI-suggested treatments
- **Dual-Language Display**: View prescriptions in English and native language with toggle
- **Medicine Database**: Comprehensive medicine information with dosages and warnings
- **Approval Workflow**: Doctor review and approval system
- **Prescription History**: Complete prescription tracking

### 🔄 Advanced Real-time Communication
- **WebSocket Integration**: Real-time messaging between doctors and patients
- **Voice Recognition**: Speech-to-text with multilingual support
- **Live Subtitles**: Real-time translation display during consultations
- **Audio Consultation**: Full-duplex voice communication with UI controls
- **Consultation Panel Toggle**: Improved UI with functional controls

### 🔐 Enhanced Authentication & Security
- **End-to-end encrypted credentials** using bcrypt hashing and JWT tokens
- Role-based access (Patient/Doctor)
- Secure signup with additional fields:
  - Patients: Age, blood group, language preference
  - Doctors: Specialization, years of experience, NMC ID, bio

### 👨‍⚕️ Enhanced Doctor Dashboard
- **Real-time notifications** via WebSocket when patients request consultations
- **Availability toggle** to control consultation availability
- **Past consultation history** with detailed reports
- **Statistics overview** (total, completed, pending consultations)
- **Profile management** with NMC verification status
- **Prescription Management**: Create, approve, and manage prescriptions

### 🧑‍⚕️ Enhanced Patient Dashboard
- **Find doctors** with advanced filtering:
  - By specialization
  - By availability
  - Search by name
- **Doctor profiles** showing:
  - Specialization
  - Years of experience
  - NMC verification status
  - Bio and availability
- **AI-powered chat** with expanded language support
- **Consultation history** with generated reports
- **Bilingual Prescription Display**: Toggle between languages
- **Language Settings**: Update preferred language
- **Consultation Controls**: Improved audio consultation UI

## 🛠️ Technical Implementation

### Backend Architecture
```
├── Flask Application (app.py)
├── AI Engine (services/ai_engine.py)
│   ├── Local Medical Database
│   ├── Groq AI Integration (Primary)
│   ├── Google Gemini Fallback
│   └── Translation Services (deep-translator)
├── Prescription Service (services/prescription_service.py)
├── Authentication (services/auth_service.py)
├── Consultation Service (services/consultation_service.py)
├── Database Layer (database.py)
└── Real-time Communication (SocketIO)
```

### External API Integrations
- **Groq AI**: Primary AI service for medical queries (Mixtral model)
- **Google Gemini**: Fallback AI service for comprehensive analysis
- **Google Translate**: Translation services with medical terminology preservation

### Database Schema
- **Users**: Patient/Doctor authentication with language preferences
- **Consultations**: Real-time consultation sessions
- **Prescriptions**: Multi-language prescription storage
- **Messages**: Chat messages with translation support
- **Reports**: Medical report generation
- **Notifications**: Real-time alerts

## 📋 Prerequisites

- Python 3.8+
- SQLite (built-in)
- Web browser with WebRTC support
- Microphone for voice consultations
- API keys for full AI functionality (optional but recommended)

## 🚀 Installation & Setup

### 1. Clone and Setup Environment
```bash
git clone <repository-url>
cd telemedicine-platform
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Create `.env` file with API keys:
```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
FLASK_DEBUG=true

# AI API Keys (optional but recommended)
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 3. Initialize Database
```bash
python -c "from database import init_db; init_db()"
```

### 4. Start Server
```bash
python app.py
```

Access the application at: http://localhost:5000

## 🔧 API Configuration

### Groq AI Setup
1. Visit [Groq Console](https://console.groq.com/)
2. Create API key
3. Add to `.env`: `GROQ_API_KEY=your-key-here`

### Google Gemini Setup
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create API key
3. Add to `.env`: `GEMINI_API_KEY=your-key-here`

## 🎯 Usage Guide

### For Patients
1. **Registration**: Create account with preferred language
2. **Doctor Selection**: Choose available specialist
3. **Consultation**: Voice/video consultation with real-time translation
4. **Prescription**: View bilingual prescriptions with language toggle
5. **Language Settings**: Update language preferences anytime

### For Doctors
1. **Dashboard**: Monitor patient queue and active consultations
2. **AI Assistance**: Use AI for symptom analysis and prescription suggestions
3. **Prescription**: Create and approve prescriptions with translation
4. **Reports**: Generate comprehensive medical reports
5. **Profile Management**: Update availability and professional details

## 🔍 Key Features Implementation

### 1. Enhanced Medical Database
```python
# AI Engine integrates multiple sources
def analyze_symptoms(transcript):
    # Local pattern matching
    local_result = analyze_local_database(transcript)

    # Enhance with AI if confidence is low
    if local_result['confidence'] < 0.6:
        ai_enhancement = query_groq_medical_info(transcript)
        local_result.update(ai_enhancement)

    return local_result
```

### 2. Prescription Translation
```python
# Automatic translation on prescription creation
def create_prescription(consultation_id, medicines, diet, exercise, notes):
    patient_lang = get_patient_language(consultation_id)

    # Translate all content
    translated_medicines = translate_medicines(medicines, patient_lang)
    translated_diet = translate_text(diet, 'en', patient_lang)
    translated_exercise = translate_text(exercise, 'en', patient_lang)

    # Store bilingual prescription
    save_prescription_with_translations(...)
```

### 3. Dual-Language Display
```javascript
// Patient dashboard bilingual toggle
function showPrescriptionLanguage(language) {
    if (language === 'english') {
        showEnglishVersion();
    } else {
        showTranslatedVersion();
    }
}
```

### 4. Audio Consultation UI Fix
```javascript
// Panel toggle functionality
function toggleConsultationPanel() {
    const panel = document.querySelector('.consultation-panel');
    panel.classList.toggle('hidden');
}
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_platform.py
```

Tests cover:
- Import validation
- AI engine functionality
- API integrations
- Database operations
- Translation services

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **API Key Protection**: Environment variable storage
- **Input Validation**: Comprehensive data validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: HTML escaping and sanitization
- **Role-based Access Control**: Patient/Doctor permissions

## 📱 Responsive Design

- **Mobile-First**: Optimized for mobile devices
- **Cross-Browser**: Compatible with modern browsers
- **Accessibility**: WCAG compliant interface
- **Progressive Enhancement**: Works without JavaScript

## 🚨 Error Handling

- **Graceful Degradation**: Functions without external APIs
- **User Feedback**: Clear error messages and status indicators
- **Fallback Systems**: Multiple AI services for redundancy
- **Logging**: Comprehensive error logging for debugging

## 🔄 Future Enhancements

- **Video Calling**: WebRTC video consultation
- **Medical Imaging**: AI-powered image analysis
- **IoT Integration**: Wearable device data
- **Blockchain**: Secure medical record storage
- **Multi-tenant**: Healthcare organization support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

---

**MediConsult** — Bridging healthcare gaps with AI and technology for accessible healthcare worldwide.