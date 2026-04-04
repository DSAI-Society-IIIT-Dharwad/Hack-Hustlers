/**
 * ═══════════════════════════════════════════════════════════════
 * Doctor Dashboard — Main Logic
 * ═══════════════════════════════════════════════════════════════
 */

let socket = null;
let voiceEngine = null;
let currentConsultation = null;
let currentPrescriptionId = null;
let auth = null;
let medicineRowCount = 0;
let notifPollTimer = null;
let autoAnalyzeTimer = null;   // debounce handle for auto-analysis

document.addEventListener('DOMContentLoaded', () => {
    auth = requireAuth('doctor');
    if (!auth) return;

    const nameEl = document.getElementById('doctor-name');
    if (nameEl) nameEl.textContent = auth.user.name;
    const titleEl = document.getElementById('welcome-title');
    if (titleEl) titleEl.textContent = `Welcome, Dr. ${auth.user.name.split(' ').slice(-1)[0]} 👋`;

    VoiceEngine.populateLanguageSelector(document.getElementById('doc-language-select'));

    initSocket();
    addMedicineRow();
    checkNotifications();
    notifPollTimer = setInterval(checkNotifications, 5000);
    loadDoctorStats();
});

// ═══ SOCKET ═══
function initSocket() {
    try {
        socket = io(API_BASE, { transports: ['websocket', 'polling'] });

        socket.on('connect', () => {
            console.log('✅ Doctor WebSocket connected');
            socket.emit('join_lobby');
            if (auth.user.role_id) {
                socket.emit('join_doctor_room', { doctor_id: auth.user.role_id });
            }
        });

        socket.on('patient_request', () => {
            showToast('A patient wants to consult with you!', 'warning', 6000);
            checkNotifications();
        });

        socket.on('new_message', (data) => {
            if (data.speaker === 'patient') {
                addDoctorTranscriptMessage('patient', data.text, data.original_text, data.timestamp, data.translated);

                if (data.urgency && data.urgency.is_urgent) {
                    showDoctorUrgencyAlert(data.urgency);
                }

                // Auto-trigger AI analysis 3 seconds after patient speaks
                clearTimeout(autoAnalyzeTimer);
                autoAnalyzeTimer = setTimeout(() => {
                    aiAutoFillPrescription(true); // silent=true → no toast if no transcript
                }, 3000);
            } else if (data.speaker === 'doctor') {
                // Doctor's own translated text echoed back
                addDoctorTranscriptMessage('doctor', data.text, data.original_text, data.timestamp, false);
            }
        });

        socket.on('urgency_alert', (data) => {
            showDoctorUrgencyAlert(data);
            showToast(data.message, 'error', 8000);
        });

        socket.on('consultation_ended', () => {
            showToast('Patient ended the consultation', 'info');
        });

        socket.on('disconnect', () => {
            console.log('❌ Doctor WebSocket disconnected');
        });
    } catch (e) {
        console.warn('WebSocket not available:', e);
    }
}

// ═══ NOTIFICATIONS ═══
async function checkNotifications() {
    try {
        const result = await apiCall('/doctors/notifications');
        if (result && result.has_notification && result.patient) {
            showNotificationBadge(result.patient);
        }
    } catch (e) {}
}

function showNotificationBadge(patient) {
    const badge = document.getElementById('notif-badge');
    badge.classList.remove('hidden');
    badge.textContent = '1';

    const content = document.getElementById('notif-content');
    content.innerHTML = `
        <div style="padding: 0.5rem 0;">
            <p style="font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">${escapeHtml(patient.name || 'Patient')}</p>
            <p class="text-sm text-muted">
                ${patient.age ? `Age: ${patient.age}` : ''}
                ${patient.gender ? `| ${patient.gender}` : ''}
                ${patient.blood_group ? `| Blood: ${patient.blood_group}` : ''}
            </p>
            <p class="text-sm mt-sm" style="color: var(--accent-secondary);">Wants to consult with you</p>
            <div class="flex gap-sm mt-md">
                <button class="btn btn-success btn-sm" onclick="acceptPatient(${patient.id})" style="flex: 1;">
                    <i class="fas fa-check"></i> Accept
                </button>
                <button class="btn btn-ghost btn-sm" onclick="declinePatient()" style="flex: 1;">
                    <i class="fas fa-times"></i> Decline
                </button>
            </div>
        </div>
    `;
}

function toggleNotificationPanel() {
    document.getElementById('notif-popup').classList.toggle('active');
}

async function acceptPatient(patientId) {
    toggleNotificationPanel();
    document.getElementById('notif-badge').classList.add('hidden');

    try {
        await apiCall('/doctors/notifications/clear', 'POST');

        const active = await apiCall('/consult/active');
        if (active && active.id) {
            currentConsultation = active;
            if (socket) {
                socket.emit('join_consultation', { consultation_id: active.id });
            }
            showConsultationView(active);
            return;
        }

        const result = await apiCall('/consult/start', 'POST', {
            patient_id: patientId,
            doctor_id: auth.user.role_id || 1
        });

        if (result && result.consultation_id) {
            const consultation = await apiCall(`/consult/${result.consultation_id}`);
            currentConsultation = consultation || { id: result.consultation_id };

            if (socket) {
                socket.emit('join_consultation', { consultation_id: result.consultation_id });
            }

            showConsultationView(currentConsultation);
        }
    } catch (e) {
        showToast('Failed to start consultation: ' + e.message, 'error');
    }
}

async function declinePatient() {
    toggleNotificationPanel();
    document.getElementById('notif-badge').classList.add('hidden');
    try { await apiCall('/doctors/notifications/clear', 'POST'); } catch (e) {}
    showToast('Patient request declined', 'info');
}

// ═══ VIEW MANAGEMENT ═══
function showConsultationView(consultation) {
    document.getElementById('view-waiting').classList.add('hidden');
    document.getElementById('view-consultation').classList.remove('hidden');
    document.getElementById('view-history').classList.add('hidden');

    if (consultation) {
        document.getElementById('patient-name-header').textContent = consultation.patient_name || 'Patient';
        const info = [];
        if (consultation.age)        info.push(`Age: ${consultation.age}`);
        if (consultation.gender)     info.push(consultation.gender);
        if (consultation.blood_group) info.push(`Blood: ${consultation.blood_group}`);
        document.getElementById('patient-info-header').textContent = info.join(' | ');

        // Replay existing transcript
        if (consultation.transcript) {
            consultation.transcript.split('\n').forEach(line => {
                const match = line.match(/^\[(\w+)\]:\s*(.+)$/);
                if (match) addDoctorTranscriptMessage(match[1].toLowerCase(), match[2], null, null, false);
            });
        }
    }
}

function showWaitingView() {
    document.getElementById('view-waiting').classList.remove('hidden');
    document.getElementById('view-consultation').classList.add('hidden');
    document.getElementById('view-history').classList.add('hidden');
}

// ═══ AVAILABILITY ═══
async function toggleAvailability(available) {
    try {
        await apiCall('/doctors/availability', 'POST', { available });
        document.getElementById('stat-status').textContent = available ? 'Available' : 'Unavailable';
        document.getElementById('stat-status').style.color  = available ? 'var(--success)' : 'var(--danger)';
        showToast(`Status: ${available ? 'Available' : 'Unavailable'}`, available ? 'success' : 'warning');
    } catch (e) {}
}

// ═══ TRANSCRIPT ═══
function addDoctorTranscriptMessage(speaker, text, originalText, timestamp, wasTranslated) {
    const container = document.getElementById('doc-transcript-container');
    const empty = document.getElementById('doc-transcript-empty');
    if (empty) empty.remove();

    const isPatient  = speaker === 'patient';
    const label      = isPatient ? (currentConsultation?.patient_name || 'Patient') : 'You';
    const icon       = isPatient ? '👤' : '🩺';
    const bubbleClass= isPatient ? 'patient-msg' : 'doctor-msg';

    let translationBadge = '';
    if (wasTranslated && originalText && originalText !== text) {
        translationBadge = `
            <div style="margin-top:4px;">
                <span class="badge badge-info" style="font-size:0.6rem;margin-right:4px;">🌐 Translated</span>
                <span style="font-size:0.7rem;color:var(--text-muted);font-style:italic;">Original: ${escapeHtml(originalText)}</span>
            </div>`;
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
    document.getElementById('doc-subtitle-text').textContent = text;
}

// ═══ DOCTOR VOICE ═══
function toggleDoctorRecording() {
    if (!voiceEngine) {
        const lang = document.getElementById('doc-language-select').value;
        voiceEngine = new VoiceEngine({
            language: lang,
            onTranscript: handleDoctorTranscript,
            onInterim: (text) => { document.getElementById('doc-subtitle-text').textContent = text; },
            onStatusChange: handleDoctorVoiceStatus,
            onError: (err) => showToast(err, 'error')
        });
    }

    if (voiceEngine.isRecording) {
        voiceEngine.stop();
        document.getElementById('doc-mic-btn').classList.remove('recording');
        document.getElementById('doc-mic-icon').className = 'fas fa-microphone';
        document.getElementById('doc-mic-status').className = 'mic-status';
        document.getElementById('doc-mic-status').textContent = 'Click to respond to patient';
        document.getElementById('doc-waveform').classList.add('hidden');
        document.getElementById('doc-subtitle-dot').classList.add('hidden');
    } else {
        voiceEngine.start();
        document.getElementById('doc-mic-btn').classList.add('recording');
        document.getElementById('doc-mic-icon').className = 'fas fa-stop';
        document.getElementById('doc-mic-status').className = 'mic-status recording';
        document.getElementById('doc-mic-status').textContent = '🔴 Recording...';
        document.getElementById('doc-waveform').classList.remove('hidden');
        document.getElementById('doc-subtitle-dot').classList.remove('hidden');
    }
}

function changeDoctorLanguage(lang) { if (voiceEngine) voiceEngine.setLanguage(lang); }

function handleDoctorTranscript(data) {
    // Rely exclusively on the WebSocket bounce-back so both ends are synchronous
    if (socket && currentConsultation) {
        socket.emit('send_message', {
            consultation_id: currentConsultation.id,
            speaker: 'doctor',
            text: data.translated,
            original_text: data.original,
            language: data.language,
            timestamp: data.timestamp
        });
    }
}

function handleDoctorVoiceStatus(status) {
    if (status === 'stopped') document.getElementById('doc-subtitle-text').textContent = 'Microphone stopped';
}

// ═══ URGENCY ═══
function showDoctorUrgencyAlert(urgency) {
    const alert   = document.getElementById('doc-urgency-alert');
    const severity = urgency.severity || 'medium';
    alert.className = `urgency-alert ${severity} active`;
    document.getElementById('doc-urgency-icon').textContent    = severity === 'critical' ? '🚨' : '⚠️';
    document.getElementById('doc-urgency-message').textContent =
        urgency.alert_message || urgency.message ||
        `Urgent keywords: ${(urgency.keywords || urgency.keywords_found || []).join(', ')}`;

    if (severity === 'critical') {
        try {
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.value = 800;
            osc.connect(ctx.destination);
            osc.start();
            setTimeout(() => osc.stop(), 500);
        } catch (e) {}
    }
}

// ═══ AI AUTO-FILL ═══════════════════════════════════════════════
/**
 * One-click: fetch AI prescription draft from transcript,
 * populate the entire prescription form, and show the analysis banner.
 * @param {boolean} silent - if true, don't show "no transcript" toast
 */
async function aiAutoFillPrescription(silent = false) {
    if (!currentConsultation) return;

    const btn = document.getElementById('ai-autofill-btn');
    const originalBtnHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    btn.disabled = true;

    try {
        const data = await apiCall(`/prescription/ai-suggest/${currentConsultation.id}`);

        if (!data || data.error) {
            if (!silent) showToast(data?.error || 'AI analysis failed', 'warning');
            return;
        }

        // ── Update analysis banner ──
        _updateAnalysisBanner(data);

        // ── Pre-fill medicines ──
        if (data.medicines && data.medicines.length > 0) {
            // Clear existing rows
            document.getElementById('medicines-container').innerHTML = '';
            medicineRowCount = 0;

            data.medicines.forEach(m => {
                addMedicineRow(m.name, m.dosage, m.frequency, m.duration || '');
            });

            // Show suggestion panel note
            const panel = document.getElementById('ai-suggestions');
            const list  = document.getElementById('ai-suggestion-list');
            panel.classList.remove('hidden');
            list.innerHTML = `<p class="text-xs text-muted" style="padding: 4px 0;">
                <i class="fas fa-info-circle"></i> ${escapeHtml(data.note || 'AI-suggested. Please review before approving.')}
            </p>`;
        }

        // ── Pre-fill diet + exercise + tests ──
        if (data.diet)     document.getElementById('diet-input').value     = data.diet;
        if (data.exercise) document.getElementById('exercise-input').value = data.exercise;
        if (data.tests && data.tests.length > 0) {
            document.getElementById('tests-input').value = data.tests.join('\n');
        }

        if (!silent) showToast('✅ AI has pre-filled the prescription. Please review before approving.', 'success', 5000);

    } catch (e) {
        if (!silent) showToast('AI Auto-Fill failed: ' + e.message, 'error');
    } finally {
        btn.innerHTML = originalBtnHtml;
        btn.disabled  = false;
    }
}

function _updateAnalysisBanner(data) {
    const banner = document.getElementById('ai-prefill-banner');
    banner.classList.add('active');

    // Urgency
    const urgencyEl = document.getElementById('ai-banner-urgency');
    if (data.urgency && data.urgency.severity !== 'low') {
        const sev = data.urgency.severity;
        urgencyEl.innerHTML = `
            <div class="urgency-inline ${sev}">
                <span>${sev === 'critical' ? '🚨' : sev === 'high' ? '⚠️' : 'ℹ️'}</span>
                <span>${escapeHtml(data.urgency.alert_message || `${sev.toUpperCase()} urgency detected`)}</span>
            </div>`;
    } else {
        urgencyEl.innerHTML = `<div class="urgency-inline low">✅ No urgent symptoms detected</div>`;
    }

    // Diagnosis + confidence
    const pct = Math.round((data.confidence || 0) * 100);
    const confColor = pct >= 70 ? '#22c55e' : pct >= 40 ? '#eab308' : '#ef4444';
    document.getElementById('ai-banner-diagnosis').textContent   = data.diagnosis || 'Requires evaluation';
    document.getElementById('ai-banner-confidence').innerHTML    = `<span style="color:${confColor};">${pct}%</span> confidence`;
    document.getElementById('ai-banner-cause').textContent       = data.cause || '—';

    // Symptoms chips
    const chips = document.getElementById('ai-banner-symptoms');
    if (data.symptoms && data.symptoms.length > 0) {
        chips.innerHTML = data.symptoms.map(s =>
            `<span class="badge badge-info" style="font-size:0.7rem;">${escapeHtml(s)}</span>`
        ).join('');
    } else {
        chips.innerHTML = '<span class="text-xs text-muted">No specific symptoms matched</span>';
    }
}

// ── Legacy: kept for "Analyze" button in transcript header ──
async function analyzeCurrentTranscript() {
    await aiAutoFillPrescription(false);
}

// ═══ PRESCRIPTION EDITOR ═══
function addMedicineRow(name = '', dosage = '', frequency = '', duration = '') {
    medicineRowCount++;
    const container = document.getElementById('medicines-container');
    const row = document.createElement('div');
    row.className = 'medicine-row';
    row.id = `med-row-${medicineRowCount}`;
    row.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;padding:0.85rem;background:var(--bg-elevated);border:1px solid var(--border-color);border-radius:var(--radius-md);margin-bottom:0.6rem;position:relative;';
    row.innerHTML = `
        <div class="form-group" style="margin-bottom:0;">
            <label class="form-label">Medicine</label>
            <input type="text" class="form-input med-name" placeholder="e.g. Paracetamol" value="${escapeHtml(name)}"
                   onblur="verifyMedicine(this, ${medicineRowCount})">
            <span class="medicine-verify-badge" id="verify-badge-${medicineRowCount}"></span>
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label class="form-label">Dosage</label>
            <input type="text" class="form-input med-dosage" placeholder="e.g. 500mg" value="${escapeHtml(dosage)}">
        </div>
        <div class="form-group" style="margin-bottom:0;">
            <label class="form-label">Frequency</label>
            <input type="text" class="form-input med-frequency" placeholder="e.g. Twice daily" value="${escapeHtml(frequency)}">
        </div>
        <div class="form-group" style="margin-bottom:0;display:flex;gap:6px;align-items:flex-end;">
            <div style="flex:1;">
                <label class="form-label">Duration</label>
                <input type="text" class="form-input med-duration" placeholder="e.g. 5 days" value="${escapeHtml(duration)}">
            </div>
            <button class="btn btn-danger btn-icon btn-sm" onclick="removeMedicineRow(${medicineRowCount})" title="Remove" style="margin-bottom:1px;flex-shrink:0;">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(row);
    if (name) {
        const input = row.querySelector('.med-name');
        verifyMedicine(input, medicineRowCount);
    }
}

function removeMedicineRow(id) {
    const row = document.getElementById(`med-row-${id}`);
    if (row) row.remove();
}

async function verifyMedicine(input, rowId) {
    const name = input.value.trim();
    if (!name) return;

    const badge = document.getElementById(`verify-badge-${rowId}`);
    badge.textContent = 'Verifying...';
    badge.className   = 'medicine-verify-badge';

    try {
        const result = await apiCall('/prescription/verify', 'POST', { name });
        if (result && result.valid) {
            badge.textContent = `✓ ${result.category}`;
            badge.className   = 'medicine-verify-badge verified';

            const row = document.getElementById(`med-row-${rowId}`);
            const dosageInput = row.querySelector('.med-dosage');
            const freqInput   = row.querySelector('.med-frequency');
            if (!dosageInput.value && result.suggested_dosage) dosageInput.value = result.suggested_dosage;
            if (!freqInput.value   && result.frequency)        freqInput.value   = result.frequency;

            if (result.warnings && result.warnings.length > 0) {
                showToast(`⚠️ ${name}: ${result.warnings[0]}`, 'warning', 5000);
            }
        } else {
            badge.textContent = '⚠ Not in database';
            badge.className   = 'medicine-verify-badge unverified';
        }
    } catch (e) {
        badge.textContent = '? Unavailable';
        badge.className   = 'medicine-verify-badge unverified';
    }
}

function collectMedicines() {
    const medicines = [];
    document.querySelectorAll('.medicine-row').forEach(row => {
        const name = row.querySelector('.med-name')?.value.trim();
        if (name) {
            medicines.push({
                name,
                dosage:    row.querySelector('.med-dosage')?.value.trim()    || '',
                frequency: row.querySelector('.med-frequency')?.value.trim() || '',
                duration:  row.querySelector('.med-duration')?.value.trim()  || ''
            });
        }
    });
    return medicines;
}

async function savePrescription() {
    if (!currentConsultation) { showToast('No active consultation', 'warning'); return; }

    const medicines = collectMedicines();
    const diet      = document.getElementById('diet-input').value.trim();
    const exercise  = document.getElementById('exercise-input').value.trim();
    const tests     = document.getElementById('tests-input').value.trim();
    const notes     = document.getElementById('notes-input').value.trim();

    const finalNotes = tests ? `Required Tests:\n${tests}\n\n${notes}` : notes;

    if (medicines.length === 0) { showToast('Please add at least one medicine', 'warning'); return; }

    try {
        const result = await apiCall('/prescription/create', 'POST', {
            consultation_id: currentConsultation.id,
            medicines,
            diet,
            exercise,
            notes: finalNotes
        });
        if (result && result.success) showToast('Prescription saved as draft', 'success');
    } catch (e) {
        showToast('Failed to save: ' + e.message, 'error');
    }
}

// ═══ APPROVE + GENERATE REPORT (one action) ═══════════════════
async function approveAndGenerateReport() {
    if (!currentConsultation) { showToast('No active consultation', 'warning'); return; }

    const btn = document.getElementById('approve-btn');
    btn.disabled  = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    try {
        // 1. Save prescription
        await savePrescription();

        // 2. Get prescription and approve it
        const prescription = await apiCall(`/prescription/${currentConsultation.id}`);
        if (!prescription || !prescription.id) {
            showToast('No prescription found. Please add medicines first.', 'warning');
            return;
        }

        const approveResult = await apiCall(`/prescription/approve/${prescription.id}`, 'POST');
        if (!approveResult || !approveResult.success) {
            showToast('Prescription approval failed', 'error');
            return;
        }

        // 3. Auto-generate the report
        const reportResult = await apiCall('/report/generate', 'POST', {
            consultation_id: currentConsultation.id
        });

        if (reportResult && reportResult.success) {
            showToast('✅ Prescription approved & report generated! Opening report...', 'success', 5000);
            // Small delay so toast is visible before new tab opens
            setTimeout(() => {
                window.open(`/report/${currentConsultation.id}`, '_blank');
            }, 800);
        } else {
            showToast('✅ Prescription approved! Report generation had an issue.', 'warning');
        }

    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    } finally {
        btn.disabled  = false;
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Approve &amp; Generate Report';
    }
}

// ═══ END CONSULTATION ═══
async function endConsultation() {
    if (!currentConsultation) return;
    if (!confirm('End this consultation? The patient will be notified.')) return;

    if (voiceEngine && voiceEngine.isRecording) voiceEngine.stop();

    try { await apiCall(`/consult/${currentConsultation.id}/complete`, 'POST'); } catch (e) {}

    if (socket) socket.emit('leave_consultation', { consultation_id: currentConsultation.id });

    clearTimeout(autoAnalyzeTimer);
    currentConsultation = null;
    showToast('Consultation ended', 'info');
    showWaitingView();
    loadDoctorStats();

    // Reset prescription form
    document.getElementById('medicines-container').innerHTML = '';
    medicineRowCount = 0;
    addMedicineRow();
    document.getElementById('diet-input').value     = '';
    document.getElementById('exercise-input').value = '';
    document.getElementById('notes-input').value    = '';
    document.getElementById('ai-prefill-banner').classList.remove('active');
    document.getElementById('ai-suggestions').classList.add('hidden');
}

// ═══ STATS ═══
async function loadDoctorStats() {
    try {
        const result = await apiCall('/history/doctor');
        if (result && result.consultations) {
            const total = result.consultations.length;
            const today = new Date().toDateString();
            const todayCount = result.consultations.filter(c =>
                new Date(c.created_at).toDateString() === today
            ).length;
            const totalEl = document.getElementById('stat-total');
            const todayEl = document.getElementById('stat-today');
            if (totalEl) totalEl.textContent = total;
            if (todayEl) todayEl.textContent = todayCount;
        }
    } catch (e) {}
}

// ═══ HISTORY ═══
async function loadDoctorHistory() {
    document.getElementById('view-waiting').classList.add('hidden');
    document.getElementById('view-history').classList.remove('hidden');

    const list = document.getElementById('doc-history-list');
    list.innerHTML = '<div class="text-center"><span class="spinner"></span><p class="text-sm text-muted mt-sm">Loading history...</p></div>';

    try {
        const result = await apiCall('/history/doctor');
        if (!result || !result.consultations || result.consultations.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><p>No past consultations yet</p></div>';
            return;
        }

        list.innerHTML = result.consultations.map(c => {
            const urgencyColor = c.urgency_level === 'critical' ? 'badge-danger'
                               : c.urgency_level === 'high'     ? 'badge-warning'
                               : c.urgency_level === 'medium'   ? 'badge-info'
                               : 'badge-neutral';
            return `
            <div class="history-item" onclick="this.classList.toggle('open')">
                <div class="history-header">
                    <div class="history-header-left">
                        <span class="badge ${urgencyColor}">${c.urgency_level || 'low'}</span>
                        <div>
                            <div style="font-weight:600;font-size:0.9rem;">${escapeHtml(c.patient_name || 'Patient')}</div>
                            <div class="text-xs text-muted">
                                ${c.age ? `Age ${c.age}` : ''} ${c.gender || ''} — ${formatDate(c.created_at)}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-sm">
                        <span class="badge ${c.status === 'completed' ? 'badge-success' : 'badge-neutral'}">${c.status}</span>
                        <span class="history-chevron"><i class="fas fa-chevron-down"></i></span>
                    </div>
                </div>
                <div class="history-body">
                    ${c.disease ? `<p class="text-sm"><strong>Diagnosis:</strong> ${escapeHtml(c.disease)}</p>` : ''}
                    ${c.symptoms ? `<p class="text-sm mt-sm"><strong>Symptoms:</strong> ${escapeHtml(c.symptoms)}</p>` : ''}
                    ${c.problem  ? `<p class="text-sm mt-sm text-muted">${escapeHtml(c.problem)}</p>` : ''}
                    <div class="flex gap-sm mt-md">
                        <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); window.open('/report/${c.id}', '_blank');">
                            <i class="fas fa-file-medical"></i> View Report
                        </button>
                    </div>
                </div>
            </div>`;
        }).join('');
    } catch (e) {
        list.innerHTML = '<div class="empty-state"><p>Could not load history</p></div>';
    }
}

// ═══ LOGOUT ═══
function handleLogout() {
    clearAuth();
    if (socket) socket.disconnect();
    if (notifPollTimer) clearInterval(notifPollTimer);
    window.location.href = '/';
}
