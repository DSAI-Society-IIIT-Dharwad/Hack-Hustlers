/**
 * ═══════════════════════════════════════════════════════════════
 * Patient Dashboard — Main Logic
 * Doctor selection, consultation, voice, prescriptions, history
 * ═══════════════════════════════════════════════════════════════
 */

let socket = null;
let voiceEngine = null;
let currentConsultation = null;
let currentDoctor = null;
let transcriptMessages = [];
let auth = null;

document.addEventListener('DOMContentLoaded', () => {
    auth = requireAuth('patient');
    if (!auth) return;

    document.getElementById('user-name').textContent = auth.user.name;
    const welcome = document.getElementById('patient-welcome');
    if (welcome) welcome.textContent = `Hello, ${auth.user.name.split(' ')[0]} 👋`;

    VoiceEngine.populateLanguageSelector(document.getElementById('language-select'));
    populateHeaderLanguageSelector();

    initSocket();
    loadDoctors();
    loadPatientStats();
});

// ═══ SOCKET ═══
function initSocket() {
    try {
        socket = io(API_BASE, { transports: ['websocket', 'polling'] });

        socket.on('connect', () => {
            console.log('✅ WebSocket connected');
            socket.emit('join_lobby');
        });

        socket.on('doctor_availability_changed', (data) => {
            loadDoctors(); // refresh doctor list
        });

        socket.on('new_message', async (data) => {
            if (data.speaker === 'patient') {
                // Show own message back — original language + server's English translation
                addTranscriptMessage('patient', data.text, data.original_text, data.timestamp, data.translated);
            } else if (data.speaker === 'doctor') {
                const targetLangKey  = document.getElementById('language-select').value;
                const targetLangCode = (LANGUAGES[targetLangKey] || {}).code || 'en-US';
                let displayText  = data.text;
                let originalText = data.original_text || data.text;
                let wasTranslated = false;

                // Translate the doctor's English reply into the patient's selected language
                if (targetLangKey !== 'en') {
                    try {
                        const res = await apiCall('/analyse/translate', 'POST', {
                            text: data.text,
                            source_lang: 'en',
                            target_lang: targetLangKey
                        });
                        if (res && res.translated && res.translated !== data.text) {
                            originalText  = data.text;
                            displayText   = res.translated;
                            wasTranslated = true;
                        }
                    } catch (e) {
                        console.warn('Could not translate doctor message:', e);
                    }
                }

                addTranscriptMessage('doctor', displayText, originalText, data.timestamp, wasTranslated);

                // Speak the translated text in the patient's language
                if (voiceEngine) {
                    voiceEngine.speak(displayText, targetLangCode);
                }
            }

            // Show urgency alert if triggered
            if (data.urgency && data.urgency.is_urgent) {
                showUrgencyAlert(data.urgency);
            }
        });

        socket.on('user_typing', (data) => {
            if (data.speaker === 'doctor') {
                document.getElementById('typing-indicator').classList.remove('hidden');
            }
        });

        socket.on('user_stopped_typing', (data) => {
            document.getElementById('typing-indicator').classList.add('hidden');
        });

        socket.on('prescription_approved', (data) => {
            showToast('Doctor approved your prescription!', 'success');
            loadPrescription(data.consultation_id);
        });

        socket.on('consultation_ended', (data) => {
            showToast('Consultation has ended.', 'info');
            loadPrescription(currentConsultation?.id);
        });

        socket.on('disconnect', () => {
            console.log('❌ WebSocket disconnected');
        });
    } catch (e) {
        console.warn('WebSocket not available:', e);
    }
}

// ═══ DOCTOR SELECTION ═══
// Store doctor data for click handling
let doctorsData = [];

async function loadPatientStats() {
    if (!auth.user.role_id) return; // no patient record yet
    try {
        const result = await apiCall(`/history/patient/${auth.user.role_id}`);
        if (result) {
            const el  = document.getElementById('stat-consultations');
            const elR = document.getElementById('stat-reports');
            if (el)  el.textContent  = (result.consultations || []).length;
            if (elR) elR.textContent = (result.reports || []).length;
        }
    } catch (e) {}
}

async function loadDoctors() {
    const grid = document.getElementById('doctor-grid');

    try {
        const result = await apiCall('/doctors/list');
        if (!result || !result.doctors) {
            renderOfflineDoctors(grid);
            return;
        }

        doctorsData = result.doctors;
        const availableCount = doctorsData.filter(d => d.available).length;
        const statEl = document.getElementById('stat-available');
        if (statEl) statEl.textContent = availableCount;

        if (doctorsData.length === 0) {
            grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🩺</div><p>No doctors registered yet</p></div>';
            return;
        }

        renderDoctorCards(grid, doctorsData);

    } catch (e) {
        console.error('Failed to load doctors:', e);
        renderOfflineDoctors(grid);
    }
}

function renderDoctorCards(grid, doctors) {
    grid.innerHTML = doctors.map(doc => `
        <div class="doctor-card ${doc.available ? '' : 'unavailable'}"
             data-doctor-id="${doc.doctor_id}"
             data-doctor-name="${doc.name.replace(/"/g, '&quot;')}"
             data-doctor-spec="${(doc.specialization || '').replace(/"/g, '&quot;')}"
             data-available="${doc.available ? '1' : '0'}"
             id="doctor-card-${doc.doctor_id}">
            <div class="doctor-status">
                ${doc.available
                    ? '<span class="badge badge-success"><span class="badge-dot badge-dot-success"></span> Available</span>'
                    : '<span class="badge badge-neutral"><span class="badge-dot badge-dot-danger"></span> Unavailable</span>'
                }
            </div>
            <div class="doctor-avatar">${getInitials(doc.name)}</div>
            <div class="doctor-name">${escapeHtml(doc.name)}</div>
            <div class="doctor-spec">${escapeHtml(doc.specialization || '')}</div>
            <div class="doctor-exp">${doc.experience_years} years experience</div>
        </div>
    `).join('');

    // Attach click handlers via delegation
    grid.querySelectorAll('.doctor-card').forEach(card => {
        card.addEventListener('click', function() {
            const available = this.dataset.available === '1';
            if (!available) {
                showToast('Doctor is currently unavailable', 'warning');
                return;
            }
            const id = parseInt(this.dataset.doctorId);
            const name = this.dataset.doctorName;
            const spec = this.dataset.doctorSpec;
            selectDoctor(id, name, spec);
        });
    });
}

function renderOfflineDoctors(grid) {
    const offlineDoctors = [
        { doctor_id: 1, name: 'Dr. Arun Sharma', specialization: 'Cardiology', experience_years: 15, available: 1 },
        { doctor_id: 2, name: 'Dr. Priya Patel', specialization: 'General Medicine', experience_years: 10, available: 1 },
        { doctor_id: 3, name: 'Dr. Rajesh Kumar', specialization: 'Neurology', experience_years: 12, available: 1 },
        { doctor_id: 4, name: 'Dr. Sneha Reddy', specialization: 'Pediatrics', experience_years: 8, available: 1 },
    ];
    renderDoctorCards(grid, offlineDoctors);
}

async function selectDoctor(doctorId, doctorName, specialization) {
    // Ensure we have a valid patient ID — never fall back to demo
    const patientId = auth.user.role_id;
    if (!patientId) {
        showToast('Your session is missing patient data. Please log out and log in again.', 'error');
        return;
    }

    currentDoctor = { id: doctorId, name: doctorName, specialization };

    // Notify the doctor with the REAL patient ID
    try {
        const notifyResult = await apiCall('/doctors/notify', 'POST', {
            doctor_id: doctorId,
            patient_id: patientId
        });
        if (notifyResult && notifyResult.error) {
            showToast(notifyResult.error, 'warning');
            return;
        }
    } catch (e) {
        console.warn('Could not notify doctor:', e);
    }

    // Start the consultation with the real patient ID
    try {
        const result = await apiCall('/consult/start', 'POST', {
            patient_id: patientId,
            doctor_id: doctorId
        });

        if (result && result.consultation_id) {
            currentConsultation = { id: result.consultation_id, doctor_id: doctorId, patient_id: patientId };
            if (socket) {
                socket.emit('join_consultation', { consultation_id: result.consultation_id });
            }
        } else {
            showToast(result?.error || 'Could not start consultation', 'error');
            return;
        }
    } catch (e) {
        showToast('Failed to start consultation: ' + e.message, 'error');
        return;
    }

    showConsultationView(doctorName, specialization);
    showToast(`Connected to ${doctorName}`, 'success');
}

// ═══ VIEW MANAGEMENT ═══
function showConsultationView(doctorName, spec) {
    document.getElementById('view-doctor-select').classList.add('hidden');
    document.getElementById('view-consultation').classList.remove('hidden');
    document.getElementById('view-history').classList.add('hidden');
    document.getElementById('history-toggle').classList.add('hidden');

    document.getElementById('consult-doctor-name').textContent = doctorName;
    document.getElementById('consult-doctor-spec').textContent = spec;

    transcriptMessages = [];
}

function showDoctorSelect() {
    document.getElementById('view-doctor-select').classList.remove('hidden');
    document.getElementById('view-consultation').classList.add('hidden');
    document.getElementById('view-history').classList.add('hidden');
    document.getElementById('history-toggle').classList.remove('hidden');
}

function backToDoctorSelect() {
    if (currentConsultation) {
        if (!confirm('Leave this consultation?')) return;
    }
    stopRecording();
    currentConsultation = null;
    currentDoctor = null;
    showDoctorSelect();
    loadDoctors();
}

// ═══ VOICE RECORDING ═══
function toggleRecording() {
    if (!voiceEngine) {
        const lang = document.getElementById('language-select').value;
        voiceEngine = new VoiceEngine({
            language: lang,
            onTranscript: handleTranscript,
            onInterim: handleInterim,
            onStatusChange: handleVoiceStatus,
            onError: (err) => showToast(err, 'error')
        });
    }

    if (voiceEngine.isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    if (voiceEngine) {
        voiceEngine.start();
        document.getElementById('mic-btn').classList.add('recording');
        document.getElementById('mic-icon').className = 'fas fa-stop';
        document.getElementById('mic-status').className = 'mic-status recording';
        document.getElementById('mic-status').textContent = '🔴 Recording... Speak now';
        document.getElementById('waveform').classList.remove('hidden');
        document.getElementById('subtitle-dot').classList.remove('hidden');
    }
}

function stopRecording() {
    if (voiceEngine) {
        voiceEngine.stop();
        document.getElementById('mic-btn').classList.remove('recording');
        document.getElementById('mic-icon').className = 'fas fa-microphone';
        document.getElementById('mic-status').className = 'mic-status';
        document.getElementById('mic-status').textContent = 'Click microphone to start speaking';
        document.getElementById('waveform').classList.add('hidden');
        document.getElementById('subtitle-dot').classList.add('hidden');
    }
}

function changeLanguage(lang) {
    if (voiceEngine) {
        voiceEngine.setLanguage(lang);
    }
}

function handleTranscript(data) {
    // Send via WebSocket FIRST (the server will broadcast it back to display it)
    if (socket && currentConsultation) {
        socket.emit('send_message', {
            consultation_id: currentConsultation.id,
            speaker: 'patient',
            text: data.translated,
            original_text: data.original,
            language: data.language,
            timestamp: data.timestamp
        });
    }

    // Update subtitle
    document.getElementById('subtitle-text').textContent = data.translated;

    // Speak translation in English (if source wasn't English)
    if (data.language !== 'en' && voiceEngine) {
        voiceEngine.speak(data.translated);
    }

    // Update AI analysis locally
    updateAIAnalysis(data.translated);
}

function handleInterim(text) {
    document.getElementById('subtitle-text').textContent = text;
}

function handleVoiceStatus(status) {
    if (status === 'stopped') {
        document.getElementById('subtitle-text').textContent = 'Microphone stopped';
    }
}

// ═══ TRANSCRIPT ═══
function addTranscriptMessage(speaker, text, originalText, timestamp, wasTranslated) {
    const container = document.getElementById('transcript-container');
    const empty = document.getElementById('transcript-empty');
    if (empty) empty.remove();

    transcriptMessages.push({ speaker, text, originalText, timestamp });

    const isPatient = speaker === 'patient';
    const label      = isPatient ? 'You' : (currentDoctor?.name || 'Doctor');
    const icon       = isPatient ? '👤' : '🩺';
    const bubbleClass= isPatient ? 'patient-msg' : 'doctor-msg';

    // Build translation info
    let translationBadge = '';
    if (wasTranslated && originalText && originalText !== text) {
        translationBadge = `
            <div style="margin-top:4px;">
                <span class="badge badge-info" style="font-size:0.6rem;margin-right:4px;">🌐 Translated</span>
                <span style="font-size:0.7rem;color:var(--text-muted);font-style:italic;">Original: ${escapeHtml(originalText)}</span>
            </div>`;
    } else if (originalText && originalText !== text) {
        translationBadge = `<div class="msg-original">Original: ${escapeHtml(originalText)}</div>`;
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = `transcript-message ${speaker}`;
    msgDiv.innerHTML = `
        <div class="msg-avatar ${isPatient ? 'patient-avatar' : 'doctor-avatar'}">${icon}</div>
        <div style="flex:1;min-width:0;">
            <div class="msg-bubble ${bubbleClass}">${escapeHtml(text)}</div>
            ${translationBadge}
            <div class="msg-meta">
                <span>${label}</span>
                <span>${timestamp || getNowTimestamp()}</span>
            </div>
        </div>
    `;

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

// ═══ AI ANALYSIS (Live — calls server) ═══
let allTranscriptText = '';
let aiAnalysisTimeout = null;

function updateAIAnalysis(newText) {
    allTranscriptText += ' ' + newText;

    // Debounce — don't spam server every word
    clearTimeout(aiAnalysisTimeout);
    aiAnalysisTimeout = setTimeout(() => _fetchAIAnalysis(allTranscriptText.trim()), 1500);
}

async function _fetchAIAnalysis(transcript) {
    const panel = document.getElementById('ai-analysis-content');
    if (!transcript || !auth) return;

    try {
        const [urgencyRes, symptomsRes] = await Promise.all([
            apiCall('/analyse/urgency',  'POST', { transcript }),
            apiCall('/analyse/symptoms', 'POST', { transcript })
        ]);

        let html = '';

        // ── Urgency Banner ──
        if (urgencyRes && urgencyRes.is_urgent) {
            const color = urgencyRes.severity === 'critical' ? 'var(--error)' : 'var(--warning)';
            html += `<div style="background:${color}18;border-left:3px solid ${color};padding:0.75rem;border-radius:6px;margin-bottom:0.75rem;">
                <strong style="color:${color};">${urgencyRes.severity === 'critical' ? '🚨 CRITICAL' : '⚠️ HIGH URGENCY'}</strong>
                <p style="font-size:0.8rem;margin-top:4px;">${escapeHtml(urgencyRes.alert_message)}</p>
            </div>`;
        }

        // ── Symptoms ──
        if (symptomsRes && symptomsRes.symptoms && symptomsRes.symptoms.length > 0) {
            html += `<div class="report-section">
                <h4 style="font-size:0.75rem;color:var(--accent-secondary);text-transform:uppercase;margin-bottom:0.5rem;">🔍 Symptoms Detected</h4>
                <div>${symptomsRes.symptoms.map(s =>
                    `<span class="badge badge-info" style="margin:2px 2px 2px 0;display:inline-block;">${escapeHtml(s)}</span>`
                ).join('')}</div>
            </div>`;
        }

        // ── Probable Diagnosis ──
        if (symptomsRes && symptomsRes.diagnosis && symptomsRes.diagnosis !== 'Requires further clinical evaluation') {
            const pct = Math.round((symptomsRes.confidence || 0) * 100);
            const barColor = pct >= 70 ? 'var(--success)' : pct >= 40 ? 'var(--warning)' : 'var(--error)';
            html += `<div class="report-section">
                <h4 style="font-size:0.75rem;color:var(--accent-secondary);text-transform:uppercase;margin-bottom:0.5rem;">🏥 Probable Condition</h4>
                <p style="font-weight:600;font-size:0.9rem;">${escapeHtml(symptomsRes.diagnosis)}</p>
                <div style="display:flex;align-items:center;gap:8px;margin-top:6px;">
                    <div style="flex:1;height:4px;background:var(--bg-input);border-radius:2px;overflow:hidden;">
                        <div style="width:${pct}%;height:100%;background:${barColor};border-radius:2px;transition:width 0.8s ease;"></div>
                    </div>
                    <span style="font-size:0.75rem;font-weight:600;color:${barColor};">${pct}% confidence</span>
                </div>
            </div>`;
        }

        // ── Precautions ──
        if (symptomsRes && symptomsRes.precautions && symptomsRes.precautions.length > 0) {
            html += `<div class="report-section">
                <h4 style="font-size:0.75rem;color:var(--accent-secondary);text-transform:uppercase;margin-bottom:0.5rem;">💡 Immediate Advice</h4>
                <ul style="padding-left:1rem;margin:0;font-size:0.82rem;color:var(--text-secondary);line-height:1.8;">
                    ${symptomsRes.precautions.slice(0,3).map(p => `<li>${escapeHtml(p)}</li>`).join('')}
                </ul>
            </div>`;
        }

        if (!html) {
            html = `<div class="empty-state" style="padding:1.5rem;">
                <div class="empty-state-icon">🤖</div>
                <p class="text-sm">Continue describing your symptoms for AI analysis.</p>
            </div>`;
        }

        panel.innerHTML = html;

    } catch (e) {
        console.warn('AI analysis error:', e);
    }
}

function showUrgencyAlert(urgency) {
    const alert = document.getElementById('urgency-alert');
    alert.className = `urgency-alert ${urgency.severity} active`;
    document.getElementById('urgency-icon').textContent = urgency.severity === 'critical' ? '🚨' : '⚠️';
    document.getElementById('urgency-message').textContent = urgency.alert_message;
}

// ═══ PRESCRIPTION ═══
async function loadPrescription(consultationId) {
    if (!consultationId) return;

    try {
        const prescription = await apiCall(`/prescription/${consultationId}`);
        if (prescription && prescription.approved) {
            displayPrescription(prescription);
        }
    } catch (e) {
        console.warn('Could not load prescription:', e);
    }
}

function displayPrescription(prescription) {
    const panel = document.getElementById('prescription-panel');
    panel.style.display = 'block';

    const content = document.getElementById('prescription-content');
    let html = '';

    // Language toggle
    const patientLang = prescription.patient_language || 'en';
    const langName = getLanguageName(patientLang);
    const hasTranslation = patientLang !== 'en' && prescription.medicines_translated;

    if (hasTranslation) {
        html += `<div class="language-toggle" style="margin-bottom: 1rem; text-align: center;">
            <div class="btn-group">
                <button class="btn btn-sm btn-primary" onclick="showPrescriptionLanguage('english')" id="btn-english">
                    English
                </button>
                <button class="btn btn-sm" onclick="showPrescriptionLanguage('translated')" id="btn-translated">
                    ${langName}
                </button>
            </div>
        </div>`;
    }

    // English version (default)
    html += '<div id="prescription-english" class="prescription-content">';
    html += '<div class="prescription-header"><h4>🏥 Prescription</h4><span class="lang-label">English</span></div>';

    if (prescription.medicines && prescription.medicines.length > 0) {
        html += '<div class="prescription-section">';
        html += '<h5>💊 Medicines</h5>';
        html += '<table class="report-table"><thead><tr><th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Duration</th></tr></thead><tbody>';
        prescription.medicines.forEach(m => {
            html += `<tr><td style="font-weight:600;">${escapeHtml(m.name)}</td><td>${escapeHtml(m.dosage)}</td><td>${escapeHtml(m.frequency)}</td><td>${escapeHtml(m.duration || '—')}</td></tr>`;
        });
        html += '</tbody></table></div>';
    }

    if (prescription.diet) {
        html += `<div class="prescription-section"><h5>🥗 Diet Recommendations</h5><p>${escapeHtml(prescription.diet)}</p></div>`;
    }
    if (prescription.exercise) {
        html += `<div class="prescription-section"><h5>🏃 Exercise Recommendations</h5><p>${escapeHtml(prescription.exercise)}</p></div>`;
    }
    if (prescription.additional_notes) {
        html += `<div class="prescription-section"><h5>📝 Additional Notes</h5><p>${escapeHtml(prescription.additional_notes)}</p></div>`;
    }
    html += '</div>';

    // Translated version (hidden by default)
    if (hasTranslation) {
        html += '<div id="prescription-translated" class="prescription-content" style="display: none;">';
        html += `<div class="prescription-header"><h4>🏥 Prescription</h4><span class="lang-label">${langName}</span></div>`;

        if (prescription.medicines_translated && prescription.medicines_translated.length > 0) {
            html += '<div class="prescription-section">';
            html += '<h5>💊 Medicines</h5>';
            html += '<table class="report-table"><thead><tr><th>Medicine</th><th>Dosage</th><th>Frequency</th><th>Duration</th></tr></thead><tbody>';
            prescription.medicines_translated.forEach(m => {
                html += `<tr><td style="font-weight:600;">${escapeHtml(m.name)}</td><td>${escapeHtml(m.dosage)}</td><td>${escapeHtml(m.frequency)}</td><td>${escapeHtml(m.duration || '—')}</td></tr>`;
            });
            html += '</tbody></table></div>';
        }

        if (prescription.diet_translated) {
            html += `<div class="prescription-section"><h5>🥗 Diet Recommendations</h5><p>${escapeHtml(prescription.diet_translated)}</p></div>`;
        }
        if (prescription.exercise_translated) {
            html += `<div class="prescription-section"><h5>🏃 Exercise Recommendations</h5><p>${escapeHtml(prescription.exercise_translated)}</p></div>`;
        }
        if (prescription.notes_translated) {
            html += `<div class="prescription-section"><h5>📝 Additional Notes</h5><p>${escapeHtml(prescription.notes_translated)}</p></div>`;
        }
        html += '</div>';
    }

    content.innerHTML = html;

    // Set initial active button
    if (hasTranslation) {
        document.getElementById('btn-english').classList.add('btn-primary');
        document.getElementById('btn-translated').classList.remove('btn-primary');
    }

    showToast('Prescription received!', 'success');
}

function showPrescriptionLanguage(language) {
    const englishDiv = document.getElementById('prescription-english');
    const translatedDiv = document.getElementById('prescription-translated');
    const btnEnglish = document.getElementById('btn-english');
    const btnTranslated = document.getElementById('btn-translated');

    if (language === 'english') {
        englishDiv.style.display = 'block';
        translatedDiv.style.display = 'none';
        btnEnglish.classList.add('btn-primary');
        btnTranslated.classList.remove('btn-primary');
    } else {
        englishDiv.style.display = 'none';
        translatedDiv.style.display = 'block';
        btnEnglish.classList.remove('btn-primary');
        btnTranslated.classList.add('btn-primary');
    }
}

function getLanguageName(code) {
    const languages = {
        'en': 'English', 'hi': 'Hindi', 'kn': 'Kannada', 'te': 'Telugu',
        'ta': 'Tamil', 'ml': 'Malayalam', 'mr': 'Marathi', 'gu': 'Gujarati',
        'es': 'Spanish', 'fr': 'French', 'de': 'German'
    };
    return languages[code] || code.toUpperCase();
}

function viewReport() {
    if (currentConsultation) {
        window.open(`/report/${currentConsultation.id}`, '_blank');
    }
}

// ═══ HISTORY ═══
async function loadHistory() {
    document.getElementById('view-doctor-select').classList.add('hidden');
    document.getElementById('view-history').classList.remove('hidden');

    const list = document.getElementById('history-list');
    list.innerHTML = '<div class="text-center"><span class="spinner"></span></div>';

    if (!auth.user.role_id) {
        list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚠️</div><p>Could not determine your patient ID. Please log out and log back in.</p></div>';
        return;
    }

    try {
        const result = await apiCall(`/history/patient/${auth.user.role_id}`);
        if (!result || !result.consultations || result.consultations.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><p>No past consultations found</p></div>';
            return;
        }

        list.innerHTML = result.consultations.map(c => `
            <div class="history-item" onclick="this.classList.toggle('open')">
                <div class="history-header">
                    <div class="history-header-left">
                        <span class="badge ${c.urgency_level === 'critical' ? 'badge-danger' : c.urgency_level === 'high' ? 'badge-warning' : 'badge-info'}">${c.urgency_level || 'low'}</span>
                        <div>
                            <div style="font-weight: 600; font-size: 0.9rem;">${escapeHtml(c.doctor_name)}</div>
                            <div class="text-xs text-muted">${c.specialization} — ${formatDate(c.created_at)}</div>
                        </div>
                    </div>
                    <div class="flex items-center gap-sm">
                        <span class="badge ${c.status === 'completed' ? 'badge-success' : 'badge-neutral'}">${c.status}</span>
                        <span class="history-chevron"><i class="fas fa-chevron-down"></i></span>
                    </div>
                </div>
                <div class="history-body">
                    <p class="text-sm"><strong>Problem:</strong> ${escapeHtml(c.problem || 'N/A')}</p>
                    <p class="text-sm mt-sm"><strong>Diagnosis:</strong> ${escapeHtml(c.disease || 'N/A')}</p>
                    <button class="btn btn-primary btn-sm mt-md" onclick="event.stopPropagation(); window.open('/report/${c.id}', '_blank');">
                        <i class="fas fa-file-medical"></i> View Report
                    </button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = '<div class="empty-state"><p>Could not load history</p></div>';
    }
}

// ═══ CONSULTATION END ═══
async function endConsultation() {
    if (!currentConsultation) return;
    if (!confirm('Are you sure you want to end this consultation?')) return;

    stopRecording();

    try {
        await apiCall(`/consult/${currentConsultation.id}/complete`, 'POST');
    } catch (e) {
        console.warn('Could not end consultation on server:', e);
    }

    if (socket) {
        socket.emit('leave_consultation', { consultation_id: currentConsultation.id });
    }

    showToast('Consultation ended', 'info');
    loadPrescription(currentConsultation.id);
}

// ═══ PANEL TOGGLE ═══
function toggleConsultationPanel() {
    const rightPanel = document.querySelector('.grid-main > div:last-child');
    const toggleIcon = document.getElementById('panel-toggle-icon');

    if (rightPanel.style.display === 'none') {
        rightPanel.style.display = 'block';
        toggleIcon.className = 'fas fa-chevron-right';
    } else {
        rightPanel.style.display = 'none';
        toggleIcon.className = 'fas fa-chevron-left';
    }
}

// ═══ LANGUAGE MANAGEMENT ═══
function populateHeaderLanguageSelector() {
    const select = document.getElementById('header-language-select');
    if (!select) return;

    select.innerHTML = '';
    for (const [key, lang] of Object.entries(LANGUAGES)) {
        const opt = document.createElement('option');
        opt.value = key;
        opt.textContent = `${lang.flag} ${lang.name}`;
        select.appendChild(opt);
    }

    // Set current user's language
    if (auth && auth.user && auth.user.profile && auth.user.profile.preferred_language) {
        select.value = auth.user.profile.preferred_language;
    }
}

async function updatePatientLanguage(language) {
    try {
        const result = await apiCall('/auth/update-language', 'POST', { language });
        if (result && result.success) {
            showToast('Language preference updated!', 'success');
            // Update auth object
            if (auth.user.profile) {
                auth.user.profile.preferred_language = language;
            }
        } else {
            showToast('Failed to update language', 'error');
        }
    } catch (e) {
        showToast('Failed to update language', 'error');
    }
}

// ═══ LOGOUT ═══
function handleLogout() {
    clearAuth();
    if (socket) socket.disconnect();
    window.location.href = '/';
}
