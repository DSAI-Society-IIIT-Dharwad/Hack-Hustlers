# MediConsult Enhanced Deployment & Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r ../requirements.txt
```

### 2. Run Enhanced Backend
```bash
cd backend
python enhanced_app.py
```

The server will start on `http://localhost:5000`

### 3. Access Frontend
- Patient Portal: `http://localhost:5000/patient_dashboard.html`
- Doctor Portal: `http://localhost:5000/doctor_dashboard.html` 
- Login: `http://localhost:5000/`

---

## Features Implemented

### FIXED ✅
- **Session Management**: Robust token validation and session tracking
- **Consultation Flow**: Fixed logout issues, proper consultation creation
- **Error Handling**: Comprehensive error messages and logging
- **Database**: Scalable in-memory mock database (ready for real DB migration)

### NEW FEATURES ✅
- **Real-time Notifications**: Socket.IO for instant consultation requests
- **Doctor Acceptance**: One-click consultation acceptance with live updates
- **Voice Input (ASR)**: Microphone button for voice-to-text conversion
- **Prescription Generation**: Doctor-side prescription template generation
- **PDF Export**: Patient & doctor reports with PDF download
- **Report Generation**: Automatic consultation reports from transcripts

### IN PROGRESS 🔄
- **Multilingual Translation**: Backend support for EN/HI/KN
- **Advanced ASR**: Google Cloud Speech-to-Text integration
- **Structured Data**: Auto-extraction of medical data from conversations
- **Conversation Intelligence**: Context retention and intent recognition

---

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register patient or doctor
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user

### Patient Routes
- `GET /api/patient/doctors` - List all doctors
- `GET /api/patient/profile` - Get patient profile
- `GET /api/patient/consultations` - Get consultation history
- `POST /api/patient/consult` - Request consultation
- `POST /api/patient/consultations/<id>/chat` - Send message
- `GET /api/patient/consultations/<id>/messages` - Get messages

### Doctor Routes
- `GET /api/doctor/profile` - Get doctor profile
- `GET /api/doctor/notifications` - Get consultation requests
- `GET /api/doctor/consultations` - Get consultations
- `POST /api/doctor/consultations/<id>/accept` - Accept consultation
- `POST /api/doctor/consultations/<id>/chat` - Send message to patient
- `POST /api/doctor/consultations/<id>/close` - Complete consultation
- `PUT /api/doctor/availability` - Toggle availability

### WebSocket Events
- `connect` - Client connects
- `join_consultation` - Join consultation room
- `consultation_request` - Doctor receives request
- `consultation_accepted` - Patient receives acceptance
- `patient_message` - Real-time patient message
- `doctor_message` - Real-time doctor message
- `consultation_completed` - Consultation completed

---

## Test Accounts

### Sample Doctors (pre-loaded)
1. **Dr. Priya Sharma** - Cardiologist
   - Email: `priya@medic.com`
   - NMC: NMC20034521 (Verified)
   - Available: ✅

2. **Dr. Rajan Mehta** - Neurologist
   - Email: `rajan@medic.com`
   - NMC: NMC18027834 (Verified)
   - Available: ❌

3. **Dr. Ananya Rao** - Dermatologist
   - Email: `ananya@medic.com`
   - NMC: NMC21045678 (Verified)
   - Available: ✅

### Create Patient Account
- Email: Any unique email
- Role: `patient`
- Age: Optional
- Blood Group: Optional

---

## Frontend Features

### Patient Dashboard
- **Find Doctors**: Search, filter by specialization, view availability
- **Consultation Chat**: Real-time messaging with doctor
- **Voice Input**: Microphone button for speech-to-text
- **Report History**: View past consultations and reports
- **PDF Export**: Download reports as PDF or print

### Doctor Dashboard
- **Real-time Notifications**: Instant consultation request alerts
- **Overview Stats**: Dashboard with key metrics
- **Active Consultations**: Accept and manage consultations
- **Prescriptions**: Generate prescription templates
- **Availability Toggle**: Quickly change availability status
- **Patient History**: View all past consultations

---

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Socket.IO Connection Issues
- Check browser console for errors
- Ensure token is valid (stored in localStorage)
- Verify CORS is properly configured

### Missing Microphone Permission
- Allow browser access to microphone in settings
- Check browser privacy permissions
- Test with HTTPS (some browsers require it)

### Database Errors
- Data is stored in-memory; refresh clears all data
- For production, integrate with SQLite/PostgreSQL
- See `backend/app.py` for original SQLAlchemy models

---

## Configuration

### Backend Settings (in `enhanced_app.py`)
- `SECRET_KEY` - Change in production
- `CORS` - Update allowed origins
- `Socket.IO` - Adjust reconnection parameters
- `Logging` - Set DEBUG=False for production

### Frontend Settings (in `enhanced-api.js`)
- `API_BASE` - Backend URL (default: localhost:5000)
- `Socket.IO` connection parameters
- Reconnection timeout settings

---

## Next Steps: Advanced Features

### 1. Multilingual Translation
```python
# Add to backend:
from google.cloud import translate_v2
# Translate messages between languages
```

### 2. Professional ASR
```python
# Integrate Google Cloud Speech-to-Text
from google.cloud import speech_v1
# Real-time audio processing
```

### 3. Database Migration
```python
# Switch from in-memory to SQLite/PostgreSQL
from sqlalchemy import create_engine
# Update models and migrations
```

### 4. Structured Medical Data
```python
# Extract from conversation:
# - Chief Complaint
# - History of Present Illness (HPI)
# - Physical Examination
# - Assessment & Diagnosis
# - Plan & Prescriptions
```

---

## Support & Documentation

- Backend: `backend/enhanced_app.py`
- Frontend: 
  - API: `frontend/js/enhanced-api.js`
  - Patient: `frontend/js/enhanced-patient.js`
  - Doctor: `frontend/js/enhanced-doctor.js`
- Styles: `frontend/css/` (global.css, patient.css, doctor.css)

---

**Last Updated**: April 4, 2026  
**Version**: 2.0 Enhanced  
**Environment**: Demo Mode (In-memory storage)
