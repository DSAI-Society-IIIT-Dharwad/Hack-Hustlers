/* ═══════════════════════════════════════════════════════════════
   enhanced-patient.js — Patient Dashboard with Real-time + Voice Support
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async () => {

  // Auth guard
  const user = Auth.getUser();
  if (!user || user.role !== 'patient') {
    window.location.href = '/';
    return;
  }

  console.log('[Patient] Initialized for user:', user.name);

  // ── State ─────────────────────────────────────────────────────────
  let allDoctors         = [];
  let consultations      = [];
  let activeConsult      = null;
  let selectedLang       = 'en';
  let chatHistory        = [];
  let isRecording        = false;
  let mediaRecorder      = null;
  let audioChunks        = [];

  // ── DOM refs ──────────────────────────────────────────────────────
  const navItems     = document.querySelectorAll('.nav-item[data-page]');
  const pages        = document.querySelectorAll('.page-content');
  const doctorsGrid  = document.getElementById('doctors-grid');
  const chatMessages = document.getElementById('chat-messages');
  const chatInput    = document.getElementById('chat-input');
  const chatSendBtn  = document.getElementById('chat-send-btn');
  const consultModal = document.getElementById('consult-modal');

  // ── Navigation ────────────────────────────────────────────────────
  function showPage(pageId) {
    pages.forEach(p => p.classList.add('hidden'));
    navItems.forEach(n => n.classList.remove('active'));
    document.getElementById(`page-${pageId}`)?.classList.remove('hidden');
    document.querySelector(`.nav-item[data-page="${pageId}"]`)?.classList.add('active');
    document.getElementById('topbar-title').textContent =
      { doctors: 'Find Doctors', chat: 'Consultation Chat', history: 'My Consultations', profile: 'My Profile' }[pageId] || pageId;
  }

  navItems.forEach(item => item.addEventListener('click', () => showPage(item.dataset.page)));

  // ── Load doctors ──────────────────────────────────────────────────
  async function loadDoctors() {
    try {
      console.log('[Patient] Loading doctors...');
      allDoctors = await api.get('/api/patient/doctors');
      populateSpecFilter();
      renderDoctors(allDoctors);
      console.log('[Patient] Loaded', allDoctors.length, 'doctors');
    } catch (e) {
      Toast.error('Failed to load doctors', e.message);
    }
  }

  function populateSpecFilter() {
    const sel = document.getElementById('spec-filter');
    const specs = [...new Set(allDoctors.map(d => d.specialization))].sort();
    sel.innerHTML = '<option value="">All Specializations</option>' +
      specs.map(s => `<option value="${s}">${s}</option>`).join('');
  }

  function renderDoctors(list) {
    if (!list.length) {
      doctorsGrid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">🩺</div>
        <h3>No doctors found</h3>
        <p>Try a different filter</p>
      </div>`;
      return;
    }
    doctorsGrid.innerHTML = list.map(doc => `
      <div class="doctor-card">
        <div class="doctor-card-header">
          <div class="doctor-avatar">${getInitials(doc.name)}</div>
          <div class="doctor-info">
            <div class="doctor-name">${doc.name}</div>
            <div class="doctor-spec">${doc.specialization}</div>
          </div>
          <div class="doctor-avail ${doc.is_available ? 'available' : 'unavailable'}">
            <span class="dot ${doc.is_available ? 'dot-green' : 'dot-red'}"></span>
            ${doc.is_available ? 'Available' : 'Busy'}
          </div>
        </div>
        <div class="doctor-bio">${doc.bio || 'Experienced medical professional'}</div>
        <div class="doctor-card-footer">
          <span class="nmc-info">🔐 NMC Verified</span>
          <button
            class="btn btn-primary btn-sm"
            onclick="window.patientNamespace.openConsultModal(${doc.user_id}, '${escapeHtml(doc.name)}', '${escapeHtml(doc.specialization)}', ${doc.is_available})"
            ${doc.is_available ? '' : 'disabled'}>
            ${doc.is_available ? '💬 Consult Now' : '🚫 Unavailable'}
          </button>
        </div>
      </div>
    `).join('');
  }

  function applyFilters() {
    const spec = document.getElementById('spec-filter').value;
    const search = document.getElementById('search-doctors').value.toLowerCase();
    const availOnly = document.getElementById('avail-filter').classList.contains('active');

    let filtered = allDoctors.filter(d => {
      const matchSpec = !spec || d.specialization === spec;
      const matchSearch = !search || d.name.toLowerCase().includes(search) || d.specialization.toLowerCase().includes(search);
      const matchAvail = !availOnly || d.is_available;
      return matchSpec && matchSearch && matchAvail;
    });

    renderDoctors(filtered);
  }

  document.getElementById('spec-filter').addEventListener('change', applyFilters);
  document.getElementById('avail-filter').addEventListener('click', function() {
    this.classList.toggle('active');
    applyFilters();
  });
  document.getElementById('search-doctors').addEventListener('input', applyFilters);
  document.getElementById('refresh-doctors')?.addEventListener('click', async function() {
    setLoading(this, true, '🔄 Refreshing...');
    await loadDoctors();
    setLoading(this, false, '🔄 Refresh');
  });

  // ── Consultation request modal ────────────────────────────────────
  window.patientNamespace = window.patientNamespace || {};

  window.patientNamespace.openConsultModal = (doctorId, doctorName, spec, available) => {
    if (!available) {
      Toast.warning('Doctor unavailable', 'This doctor is not accepting consultations');
      return;
    }
    document.getElementById('modal-doctor-name').textContent = doctorName;
    document.getElementById('modal-doctor-spec').textContent = spec;
    document.getElementById('confirm-consult-btn').dataset.doctorId = doctorId;
    consultModal.classList.add('active');
  };

  document.getElementById('close-consult-modal').addEventListener('click', () => consultModal.classList.remove('active'));
  consultModal.addEventListener('click', e => {
    if (e.target === e.currentTarget) consultModal.classList.remove('active');
  });

  document.getElementById('confirm-consult-btn').addEventListener('click', async function() {
    const doctorId = parseInt(this.dataset.doctorId);
    const lang     = document.getElementById('modal-lang').value;
    setLoading(this, true, 'Requesting...');

    try {
      console.log('[Patient] Requesting consultation with doctor', doctorId);
      const res = await api.post('/api/patient/consult', {
        doctor_id: doctorId,
        language: lang
      });

      if (!res || !res.consultation) {
        throw new Error('Invalid response from server');
      }

      activeConsult = res.consultation;
      selectedLang  = lang;
      chatHistory   = [];

      consultModal.classList.remove('active');
      Toast.success('Consultation requested!', 'Waiting for doctor to accept...');

      // Pre-load welcome message
      chatMessages.innerHTML = '';
      appendMessage('ai', res.welcome_message, new Date().toISOString());

      await loadConsultations();

      // Join Socket.IO room for real-time updates
      joinConsultationRoom(activeConsult.id);

      // Listen for doctor acceptance
      if (socket) {
        socket.on('consultation_accepted', async (data) => {
          activeConsult.status = 'active';
          Toast.success('Accepted!', 'Dr. ' + data.consultation.doctor_name + ' has accepted your consultation');
          console.log('[Patient] Consultation accepted:', data.consultation);
          await maybeStartAutoASR();
        });

        socket.on('doctor_message', (data) => {
          if (data.consultation_id === activeConsult.id) {
            appendMessage('doctor', data.message.content, data.message.created_at);
          }
        });

        socket.on('consultation_completed', (data) => {
          activeConsult.status = 'completed';
          Toast.info('Completed', 'Your consultation has been completed');
          console.log('[Patient] Consultation completed');
        });
      }

      showPage('chat');

    } catch (e) {
      console.error('[Patient] Consultation request failed:', e);
      Toast.error('Request failed', e.message);
    } finally {
      setLoading(this, false, '✅ Start Consultation');
    }
  });

  // ── Chat interface ───────────────────────────────────────────────
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedLang = btn.dataset.lang;
    });
  });

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    if (!activeConsult) {
      Toast.warning('No active consultation', 'Start a consultation first');
      showPage('doctors');
      return;
    }

    chatInput.value = '';
    chatSendBtn.disabled = true;

    // Show patient message
    appendMessage('patient', text, new Date().toISOString());

    const typingEl = appendTyping();

    try {
      console.log('[Patient] Sending message:', text);
      const res = await api.post(`/api/patient/consultations/${activeConsult.id}/chat`, {
        message: text
      });

      typingEl.remove();

      // Emit to doctor via Socket.IO
      if (socket) {
        socket.emit('patient_message', {
          message: res.patient_message,
          consultation_id: activeConsult.id
        });
      }

      Toast.info('Sent', 'Message sent to doctor');

    } catch (e) {
      typingEl.remove();
      Toast.error('Failed to send', e.message);
      appendMessage('ai', '⚠️ Failed to send message. Please try again.', new Date().toISOString());
    } finally {
      chatSendBtn.disabled = false;
      chatInput.focus();
    }
  }

  chatSendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // ── Voice recording (ASR) ─────────────────────────────────────────
  const micBtn = document.getElementById('mic-btn');
  if (micBtn) {
    micBtn.addEventListener('click', toggleVoiceRecording);
  }

  async function toggleVoiceRecording() {
    if (isRecording) {
      stopVoiceRecording();
    } else {
      startVoiceRecording();
    }
  }

  async function startVoiceRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstart = () => {
        isRecording = true;
        if (micBtn) micBtn.classList.add('recording');
        Toast.info('Recording', 'Listening...');
        console.log('[Patient] Voice recording started');
      };

      mediaRecorder.onstop = async () => {
        isRecording = false;
        if (micBtn) micBtn.classList.remove('recording');

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        await processAudioToText(audioBlob);
      };

      mediaRecorder.start();

    } catch (error) {
      Toast.error('Microphone error', error.message);
      console.error('[Patient] Microphone access failed:', error);
    }
  }

  function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  }

  async function processAudioToText(audioBlob) {
    try {
      Toast.info('Processing', 'Converting audio to text...');

      // For now, we'll use a placeholder
      // In production, integrate with Google Cloud Speech-to-Text or similar
      // This would send the audio blob to your backend for processing

      // Mock implementation: simulate ASR processing
      const mockText = await mockSpeechToText(audioBlob);
      chatInput.value = mockText;
      chatInput.focus();

      Toast.success('Recognized', mockText);
      console.log('[Patient] Speech recognized:', mockText);

    } catch (error) {
      Toast.error('Speech recognition failed', error.message);
      console.error('[Patient] ASR error:', error);
    }
  }

  // Mock speech-to-text for demo purposes
  async function mockSpeechToText(audioBlob) {
    // In production, this would call Google Cloud Speech-to-Text API
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        // Simulated ASR result
        resolve('I have a headache and fever for the past 2 days');
      };
      reader.onerror = reject;
      reader.readAsArrayBuffer(audioBlob);
    });
  }

  async function maybeStartAutoASR() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      Toast.warning('ASR unsupported', 'Your browser does not support microphone access.');
      return;
    }

    try {
      const permission = await navigator.permissions.query({ name: 'microphone' });
      if (permission.state === 'granted') {
        await startVoiceRecording();
        Toast.success('Voice ready', 'Audio input started for your consultation.');
      } else if (permission.state === 'prompt') {
        Toast.info('Click the microphone button', 'Allow microphone access to enable voice input.');
      } else {
        Toast.warning('Microphone blocked', 'Please enable microphone permission to use ASR.');
      }
    } catch (err) {
      console.warn('[Patient] Permission check failed', err);
      try {
        await startVoiceRecording();
      } catch (e) {
        Toast.info('Click the microphone button', 'Allow microphone access to start voice input.');
      }
    }
  }

  // ── Load consultations ────────────────────────────────────────────
  async function loadConsultations() {
    try {
      console.log('[Patient] Loading consultations...');
      consultations = await api.get('/api/patient/consultations');
      renderHistory();
      console.log('[Patient] Loaded', consultations.length, 'consultations');
    } catch (e) {
      Toast.error('Failed to load history', e.message);
    }
  }

  function renderHistory() {
    const list = document.getElementById('history-list');
    if (!consultations.length) {
      list.innerHTML = `<div class="empty-state">
        <div class="empty-icon">📋</div>
        <h3>No consultations yet</h3>
        <p>Start your first consultation with a doctor</p>
      </div>`;
      return;
    }

    list.innerHTML = consultations.map(c => `
      <div class="history-card" onclick="window.patientNamespace.resumeConsult(${c.id}, '${c.status}')">
        <div class="history-icon">🏥</div>
        <div class="history-info">
          <div class="history-doctor">Dr. ${c.doctor_name}</div>
          <div class="history-meta">
            ${formatDate(c.created_at)} · ${langLabel(c.language)}
            · <span class="badge ${statusBadge(c.status)}">${c.status}</span>
          </div>
          <div class="history-preview">${c.report_text ? c.report_text.substring(0, 60) + '...' : 'Consultation in progress...'}</div>
        </div>
        ${c.report_text ? `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();window.patientNamespace.showHistoryReport('${escapeHtml(c.report_text)}')">📄 Report</button>` : ''}
      </div>
    `).join('');
  }

  window.patientNamespace.resumeConsult = async (consultId, status) => {
    const c = consultations.find(x => x.id === consultId);
    if (!c) return;
    activeConsult = c;
    selectedLang = c.language;

    chatMessages.innerHTML = '';
    try {
      const msgs = await api.get(`/api/patient/consultations/${consultId}/messages`);
      msgs.forEach(m => appendMessage(m.sender_role, m.content, m.created_at));
    } catch (e) {
      Toast.error('Failed to load chat', e.message);
    }

    joinConsultationRoom(consultId);
    showPage('chat');
  };

  let currentReportText = '';

  window.patientNamespace.showHistoryReport = (text) => {
    currentReportText = text;
    document.getElementById('history-report-content').textContent = text;
    document.getElementById('history-report-modal').classList.add('active');
  };

  document.getElementById('download-report-btn')?.addEventListener('click', () => {
    if (!currentReportText) return;
    downloadReport(currentReportText, `MediConsult_Report_${new Date().toISOString().slice(0,10)}.txt`);
  });

  document.getElementById('print-report-btn')?.addEventListener('click', () => {
    if (!currentReportText) return;
    printReport(currentReportText);
  });

  document.getElementById('close-report-modal')?.addEventListener('click', () => {
    document.getElementById('history-report-modal').classList.remove('active');
  });

  // ── Profile ───────────────────────────────────────────────────────
  document.getElementById('profile-name-disp').textContent   = user.name;
  document.getElementById('profile-email-disp').textContent  = user.email;
  document.getElementById('profile-role-disp').textContent   = 'Patient';
  document.getElementById('profile-age-disp').textContent    = user.age || 'Not specified';
  document.getElementById('profile-blood-disp').textContent  = user.blood_group || 'Not specified';
  document.getElementById('profile-avatar-disp').textContent = getInitials(user.name);
  document.getElementById('sidebar-avatar').textContent      = getInitials(user.name);
  document.getElementById('sidebar-name').textContent        = user.name;
  document.getElementById('sidebar-email').textContent       = user.email;

  // ── Logout ────────────────────────────────────────────────────────
  document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
      await api.post('/api/auth/logout', {});
    } catch (e) {
      console.warn('Logout API failed, clearing locally:', e);
    }
    Auth.clear();
    disconnectSocket();
    window.location.href = '/';
  });

  // ── Helpers ───────────────────────────────────────────────────────
  function statusBadge(status) {
    return { completed: 'badge-green', pending_acceptance: 'badge-amber', active: 'badge-cyan' }[status] || 'badge-amber';
  }

  function setLoading(btn, loading, label) {
    btn.disabled = loading;
    btn.innerHTML = loading ? '<span class="spinner"></span> ' + label : label;
  }

  function downloadReport(text, filename) {
    if (window.jspdf?.jsPDF) {
      const doc = new window.jspdf.jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth() - 32;
      const lines = doc.splitTextToSize(text, pageWidth);
      doc.setFontSize(12);
      doc.text(lines, 16, 20);
      doc.save(filename.replace(/\.txt$/i, '.pdf'));
      return;
    }

    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  function printReport(text) {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>Consultation Report</title><style>
      body { font-family: system-ui, sans-serif; padding: 24px; color: #111; }
      h1 { font-size: 24px; margin-bottom: 16px; }
      pre { white-space: pre-wrap; word-break: break-word; font-size: 14px; }
      .footer { margin-top: 32px; font-size: 12px; color: #555; }
    </style></head><body>`);
    printWindow.document.write('<h1>MediConsult Consultation Report</h1>');
    printWindow.document.write(`<pre>${escapeHtml(text)}</pre>`);
    printWindow.document.write('<div class="footer">Generated by MediConsult</div>');
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  }

  function appendMessage(role, content, timestamp) {
    const isPatient = role === 'patient';
    const el = document.createElement('div');
    el.className = `chat-message chat-${role}`;
    el.innerHTML = `
      <div class="chat-avatar">${role === 'patient' ? '👤' : role === 'doctor' ? '👨‍⚕️' : '🤖'}</div>
      <div class="chat-content">
        <div class="chat-text">${escapeHtml(content)}</div>
        <div class="chat-time">${formatDate(timestamp)}</div>
      </div>
    `;
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendTyping() {
    const el = document.createElement('div');
    el.className = 'chat-message chat-ai';
    el.innerHTML = `
      <div class="chat-avatar">🤖</div>
      <div class="chat-content">
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return el;
  }

  // ── Initialize ────────────────────────────────────────────────────
  console.log('[Patient] Starting initialization...');
  initSocket();
  await Promise.all([loadDoctors(), loadConsultations()]);
  showPage('doctors');
  console.log('[Patient] Initialization complete');

});
