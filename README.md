# MediConsult — AI Multilingual Medical Platform

A comprehensive web platform for AI-powered multilingual medical consultations connecting patients with NMC-verified doctors.

## Features

### 🔐 Authentication & Security
- **End-to-end encrypted credentials** using bcrypt hashing and JWT tokens
- Role-based access (Patient/Doctor)
- Secure signup with additional fields:
  - Patients: Age and blood group
  - Doctors: Specialization, years of experience, NMC ID, bio

### 👨‍⚕️ Doctor Dashboard
- **Real-time notifications** via WebSocket when patients request consultations
- **Availability toggle** to control consultation availability
- **Past consultation history** with text reports
- **Statistics overview** (total, completed, pending consultations)
- **Profile management** with NMC verification status

### 🧑‍⚕️ Patient Dashboard
- **Find doctors** with advanced filtering:
  - By specialization
  - By availability
  - Search by name
- **Doctor profiles** showing:
  - Specialization
  - Years of experience
  - NMC verification status
  - Bio and availability
- **AI-powered chat** in English, Hindi, and Kannada
- **Consultation history** with generated reports

### 🤖 AI Features
- **Multilingual support**: English, Hindi (हिंदी), Kannada (ಕನ್ನಡ)
- **Gemini AI integration** for medical assistance
- **Automatic language detection** and response
- **Consultation report generation** with structured medical summaries

## Tech Stack

- **Backend**: Python Flask with REST APIs
- **Database**: SQLite with SQLAlchemy ORM
- **Real-time**: Flask-SocketIO for WebSocket notifications
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **AI**: Google Gemini API
- **Security**: bcrypt + JWT

## Setup & Installation

1. **Clone/Download** the project files

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Add your `GEMINI_API_KEY` (get from Google AI Studio)
   - JWT secret is pre-configured for development

4. **Run the application**:
   ```bash
   # Windows
   start.bat

   # Or manually:
   cd backend
   python app.py
   ```

5. **Open browser** to `http://localhost:5000`

## Usage

### For Patients:
1. **Sign up/Login** with email and password
2. **Provide age and blood group** during signup
3. **Browse available doctors** by specialization and experience
4. **Start consultation** with preferred language
5. **Chat with AI assistant** for symptom description
6. **Generate consultation report** when done

### For Doctors:
1. **Sign up/Login** with professional details
2. **Set availability** to accept/reject consultations
3. **Receive real-time notifications** for new requests
4. **View consultation history** with AI-generated reports
5. **Manage profile** and NMC verification status

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login

### Doctor APIs
- `GET /api/doctor/profile` - Get doctor profile
- `PUT /api/doctor/availability` - Toggle availability
- `GET /api/doctor/notifications` - Get notifications
- `GET /api/doctor/consultations` - Get consultation history

### Patient APIs
- `GET /api/patient/doctors` - List available doctors
- `POST /api/patient/consult` - Request consultation
- `POST /api/patient/consultations/{id}/chat` - Send chat message
- `POST /api/patient/consultations/{id}/report` - Generate report

## Security Features

- **Password hashing** with bcrypt
- **JWT authentication** with expiration
- **Role-based access control**
- **Input validation** and sanitization
- **CORS protection**
- **SQL injection prevention** via ORM

## Multilingual Support

The platform supports three languages:
- **English** (en)
- **Hindi** (hi) - हिन्दी
- **Kannada** (kn) - ಕನ್ನಡ

AI responses are automatically provided in the user's language.

## Database Schema

- **Users**: Basic user info, role, credentials
- **Doctors**: Professional details, NMC verification
- **Consultations**: Chat sessions between patients and doctors
- **Messages**: Individual chat messages (patient/AI)
- **Notifications**: Real-time alerts for doctors

## Development Notes

- Uses SQLite for simplicity (can be changed to PostgreSQL/MySQL)
- WebSocket for real-time notifications
- Responsive design with mobile support
- Sample doctor data seeded on first run

## Troubleshooting

**Python 3.14 Compatibility Issue**:
If you encounter SQLAlchemy import errors with Python 3.14, try:
1. Use Python 3.12 or 3.11
2. Or update SQLAlchemy to latest version

**AI Features Not Working**:
- Ensure `GEMINI_API_KEY` is set in `.env`
- Check API quota and billing status

**Port Already in Use**:
- Change port in `app.py` from 5000 to another port

---

**MediConsult** — Bridging healthcare gaps with AI and technology.