/* ═══════════════════════════════════════════════════════════════
   enhanced-doctor.js — Doctor Dashboard with Real-time + Prescriptions
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async () => {

  // Auth guard
  const user = Auth.getUser();
  if (!user || user.role !== 'doctor') {
    window.location.href = '/';
    return;
  }

  console.log('[Doctor] Initialized for user:', user.name);

  // ── State ─────────────────────────────────────────────────────────
  let notifications   = [];
  let consultations   = [];
  let activeConsult   = null;
  let isRecording     = false;
  let mediaRecorder   = null;
  let audioChunks     = [];
  let pendingNotifications = []; // Unread notifications

  // ── DOM refs ──────────────────────────────────────────────────────
  const navItems          = document.querySelectorAll('.nav-item[data-page]');
  const pages             = document.querySelectorAll('.page-content');
  const consultTable      = document.getElementById('consult-table');
  const notificList       = document.getElementById('notif-list');
  const chatMessages      = document.getElementById('chat-messages');
  const chatInput         = document.getElementById('chat-input');
  const chatSendBtn       = document.getElementById('chat-send-btn');

  // ── Navigation ────────────────────────────────────────────────────
  function showPage(pageId) {
    pages.forEach(p => p.classList.add('hidden'));
    navItems.forEach(n => n.classList.remove('active'));
    document.getElementById(`page-${pageId}`)?.classList.remove('hidden');
    document.querySelector(`.nav-item[data-page="${pageId}"]`)?.classList.add('active');
    document.getElementById('topbar-title').textContent =
      { overview: 'Dashboard', consults: 'Consultations', notifs: 'Notifications', profile: 'My Profile' }[pageId] || pageId;
  }

  navItems.forEach(item => item.addEventListener('click', () => showPage(item.dataset.page)));

  // ── Load profile ──────────────────────────────────────────────────
  async function loadProfile() {
    try {
      console.log('[Doctor] Loading profile...');
      const profile = await api.get('/api/doctor/profile');
      user.doctor = profile.doctor;
      console.log('[Doctor] Profile loaded:', profile.name);
    } catch (e) {
      Toast.error('Failed to load profile', e.message);
    }
  }

  // ── Load stats ────────────────────────────────────────────────────
  async function loadStats() {
    try {
      const stats = {
        total_consultations: consultations.length,
        active_consultations: consultations.filter(c => c.status === 'active').length,
        completed_consultations: consultations.filter(c => c.status === 'completed').length,
        pending_notifications: notifications.filter(n => !n.is_read).length
      };

      document.getElementById('stat-total').textContent = stats.total_consultations;
      document.getElementById('stat-active').textContent = stats.active_consultations;
      document.getElementById('stat-completed').textContent = stats.completed_consultations;
      document.getElementById('stat-pending').textContent = stats.pending_notifications;

      console.log('[Doctor] Stats updated:', stats);
    } catch (e) {
      console.error('[Doctor] Failed to update stats:', e);
    }
  }

  // ── Load notifications ────────────────────────────────────────────
  async function loadNotifications() {
    try {
      console.log('[Doctor] Loading notifications...');
      notifications = await api.get('/api/doctor/notifications');
      renderNotifications();
      loadStats();
      console.log('[Doctor] Loaded', notifications.length, 'notifications');
    } catch (e) {
      Toast.error('Failed to load notifications', e.message);
    }
  }

  function renderNotifications() {
    if (!notificList) return;

    if (!notifications.length) {
      notificList.innerHTML = `<div class="empty-state">
        <div class="empty-icon">🔔</div>
        <h3>No notifications</h3>
        <p>You'll see consultation requests here</p>
      </div>`;
      return;
    }

    notificList.innerHTML = notifications.map(n => {
      if (n.type !== 'consultation_request') return '';
      return `
        <div class="notification-card ${!n.is_read ? 'unread' : ''}">
          <div class="notif-icon">🏥</div>
          <div class="notif-body">
            <div class="notif-title">${n.message}</div>
            <div class="notif-meta">
              ${n.patient_age ? `Age: ${n.patient_age}` : ''} · 
              ${n.patient_blood ? `Blood: ${n.patient_blood}` : ''}
            </div>
            <div class="notif-time">${formatDate(n.created_at)}</div>
          </div>
          <button class="btn btn-success btn-sm" onclick="window.doctorNamespace.acceptConsultation('${n.consultation_id}')">
            ✅ Accept
          </button>
        </div>
      `;
    }).join('');
  }

  // ── Load consultations ────────────────────────────────────────────
  async function loadConsultations() {
    try {
      console.log('[Doctor] Loading consultations...');
      consultations = await api.get('/api/doctor/consultations');
      renderConsultations();
      loadStats();
      console.log('[Doctor] Loaded', consultations.length, 'consultations');
    } catch (e) {
      Toast.error('Failed to load consultations', e.message);
    }
  }

  function renderConsultations() {
    if (!consultTable) return;

    if (!consultations.length) {
      consultTable.innerHTML = `<div class="empty-state">
        <div class="empty-icon">📋</div>
        <h3>No consultations yet</h3>
        <p>Accept consultation requests to start</p>
      </div>`;
      return;
    }

    consultTable.innerHTML = consultations.map(c => `
      <div class="consultation-row" onclick="window.doctorNamespace.resumeConsult('${c.id}', '${c.status}')">
        <div class="row-cell">${c.patient_name}</div>
        <div class="row-cell">${formatDate(c.created_at)}</div>
        <div class="row-cell"><span class="badge ${statusBadge(c.status)}">${c.status}</span></div>
        <div class="row-cell">
          <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();window.doctorNamespace.showHistory('${escapeHtml(c.transcript || 'No transcript')}')">
            📄 View
          </button>
        </div>
      </div>
    `).join('');
  }

  window.doctorNamespace = window.doctorNamespace || {};

  window.doctorNamespace.acceptConsultation = async (consultId) => {
    try {
      console.log('[Doctor] Accepting consultation:', consultId);
      const res = await api.post(`/api/doctor/consultations/${consultId}/accept`, {});

      activeConsult = res.consultation;
      Toast.success('Accepted!', 'Consultation is now active');

      // Join Socket.IO room
      joinConsultationRoom(consultId);

      // Listen for patient messages
      if (socket) {
        socket.on('patient_message', (data) => {
          if (data.consultation_id === consultId) {
            appendMessage('patient', data.message.content, data.message.created_at);
          }
        });
      }

      await Promise.all([loadNotifications(), loadConsultations()]);
      showPage('consults');
      await maybeStartAutoASR();

    } catch (e) {
      Toast.error('Failed to accept', e.message);
    }
  };

  window.doctorNamespace.resumeConsult = async (consultId, status) => {
    console.log('[Doctor] Resuming consultation:', consultId);
    const c = consultations.find(x => x.id === consultId);
    if (!c) return;

    activeConsult = c;
    chatMessages.innerHTML = '';

    try {
      // In a real app, fetch messages from endpoint
      // For now, show consultation info
      appendMessage('ai', `Consultation with ${c.patient_name}\nStatus: ${c.status}`, c.created_at);
    } catch (e) {
      Toast.error('Failed to load consultation', e.message);
    }

    joinConsultationRoom(consultId);
    await maybeStartAutoASR();
    showPage('consults');
  };

  window.doctorNamespace.showHistory = (transcript) => {
    const modal = document.getElementById('history-modal');
    if (modal) {
      document.getElementById('history-content').textContent = transcript;
      modal.classList.add('active');
    }
  };

  document.getElementById('close-history-modal')?.addEventListener('click', function() {
    document.getElementById('history-modal')?.classList.remove('active');
  });

  // ── Chat interface ───────────────────────────────────────────────
  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    if (!activeConsult) {
      Toast.warning('No active consultation', 'Select a consultation first');
      return;
    }

    chatInput.value = '';
    chatSendBtn.disabled = true;

    appendMessage('doctor', text, new Date().toISOString());

    try {
      console.log('[Doctor] Sending message:', text);
      const res = await api.post(`/api/doctor/consultations/${activeConsult.id}/chat`, {
        message: text
      });

      // Emit via Socket.IO
      if (socket) {
        socket.emit('doctor_message', {
          message: res.doctor_message,
          consultation_id: activeConsult.id
        });
      }

      Toast.info('Sent', 'Message sent to patient');

    } catch (e) {
      Toast.error('Failed to send', e.message);
    } finally {
      chatSendBtn.disabled = false;
      chatInput.focus();
    }
  }

  if (chatSendBtn) {
    chatSendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
  }

  // ── Voice recording (ASR) on doctor side ──────────────────────────
  const micBtn = document.getElementById('mic-btn-doctor');
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
        Toast.info('Recording', 'Recording...', 2000);
        console.log('[Doctor] Voice recording started');
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
      console.error('[Doctor] Microphone failed:', error);
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
      Toast.info('Processing', 'Converting audio to text...', 2000);

      const mockText = await mockSpeechToText(audioBlob);
      chatInput.value = mockText;
      chatInput.focus();

      Toast.success('Recognized', mockText);
      console.log('[Doctor] Speech recognized:', mockText);

    } catch (error) {
      Toast.error('Speech recognition failed', error.message);
      console.error('[Doctor] ASR error:', error);
    }
  }

  async function mockSpeechToText(audioBlob) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => {
        // Mock ASR result
        resolve('Take 2 tablets of paracetamol twice daily for 3 days. Drink lots of water and rest.');
      };
      reader.readAsArrayBuffer(audioBlob);
    });
  }

  async function maybeStartAutoASR() {
    if (!activeConsult) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      Toast.warning('ASR unsupported', 'Your browser does not support microphone access.');
      return;
    }

    try {
      const permission = await navigator.permissions.query({ name: 'microphone' });
      if (permission.state === 'granted') {
        await startVoiceRecording();
        Toast.success('Voice ready', 'Audio input started for the consultation.');
      } else if (permission.state === 'prompt') {
        Toast.info('Voice input ready', 'Click the microphone button to start audio input.');
      } else {
        Toast.warning('Microphone blocked', 'Please allow microphone access to enable ASR.');
      }
    } catch (err) {
      console.warn('[Doctor] Permission check failed', err);
      try {
        await startVoiceRecording();
      } catch (e) {
        Toast.info('Voice input ready', 'Click the microphone button to start audio input.');
      }
    }
  }

  // ── Prescription generation ───────────────────────────────────────
  function generatePrescription() {
    if (!activeConsult) {
      Toast.warning('No active consultation', 'Select a consultation first');
      return;
    }

    const drugs = prompt('Enter drug names (comma-separated)?') || '';
    const dosage = prompt('Enter dosage (e.g., 500 mg)?') || '';
    const frequency = prompt('Enter frequency (e.g., twice daily)?') || '';
    const duration = prompt('Enter duration (e.g., 5 days)?') || '';

    if (!drugs || !dosage || !frequency || !duration) {
      Toast.warning('Incomplete', 'Please fill all fields');
      return;
    }

    const prescription = `
═══════════════════════════════════════════════════════════════
                    MEDICAL PRESCRIPTION
═══════════════════════════════════════════════════════════════

PATIENT: ${activeConsult.patient_name}
DOCTOR: ${user.name}
DATE: ${new Date().toLocaleDateString()}
CONSULTATION ID: ${activeConsult.id}

───────────────────────────────────────────────────────────────
MEDICATIONS:
───────────────────────────────────────────────────────────────

Drug Name(s): ${drugs}
Dosage: ${dosage}
Frequency: ${frequency}
Duration: ${duration}

───────────────────────────────────────────────────────────────
ADDITIONAL INSTRUCTIONS:
───────────────────────────────────────────────────────────────
• Take with food
• Stay hydrated
• Get adequate rest
• Follow up if symptoms persist

───────────────────────────────────────────────────────────────
DOCTOR SIGNATURE: Dr. ${user.name}
═══════════════════════════════════════════════════════════════
`;

    // Show prescription in modal
    const modal = document.getElementById('prescription-modal');
    if (modal) {
      document.getElementById('prescription-content').textContent = prescription;
      modal.classList.add('active');

      // Add download button
      document.getElementById('download-prescription-btn')?.addEventListener('click', () => {
        downloadFile(prescription, 'prescription.txt');
      });
    }

    Toast.success('Generated', 'Prescription created');
    console.log('[Doctor] Prescription generated');
  }

  // ── Close consultation ────────────────────────────────────────────
  async function closeConsultation() {
    if (!activeConsult) {
      Toast.warning('No active consultation', 'Select a consultation first');
      return;
    }

    const confirm_close = confirm('Close this consultation and mark as completed?');
    if (!confirm_close) return;

    try {
      console.log('[Doctor] Closing consultation:', activeConsult.id);
      const res = await api.post(`/api/doctor/consultations/${activeConsult.id}/close`, {});

      activeConsult = null;
      Toast.success('Closed', 'Consultation completed');

      // Notify patient via Socket.IO
      if (socket) {
        socket.emit('consultation_completed', {
          consultation_id: res.consultation.id
        });
      }

      await loadConsultations();
      showPage('overview');

    } catch (e) {
      Toast.error('Failed to close', e.message);
    }
  }

  // ── Availability toggle ───────────────────────────────────────────
  document.getElementById('avail-toggle')?.addEventListener('click', async function() {
    try {
      const res = await api.put('/api/doctor/availability', {
        is_available: !user.doctor.is_available
      });

      user.doctor.is_available = res.is_available;
      this.classList.toggle('available');
      this.textContent = res.is_available ? '✅ Available' : '❌ Unavailable';

      Toast.success('Updated', `You are now ${res.is_available ? 'available' : 'unavailable'}`);

    } catch (e) {
      Toast.error('Failed to update', e.message);
    }
  });

  // ── Profile ───────────────────────────────────────────────────────
  if (document.getElementById('profile-name-disp')) {
    document.getElementById('profile-name-disp').textContent = user.name;
    document.getElementById('profile-email-disp').textContent = user.email;
    document.getElementById('profile-spec-disp').textContent = user.doctor?.specialization || 'General Medicine';
    document.getElementById('profile-nmc-disp').textContent = user.doctor?.nmc_id || 'N/A';
    document.getElementById('profile-years-disp').textContent = user.doctor?.years_of_experience || 0;
    document.getElementById('profile-avatar-disp').textContent = getInitials(user.name);
    document.getElementById('sidebar-avatar').textContent = getInitials(user.name);
    document.getElementById('sidebar-name').textContent = user.name;
    document.getElementById('sidebar-email').textContent = user.email;
  }

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
    return {
      pending_acceptance: 'badge-amber',
      active: 'badge-cyan',
      completed: 'badge-green',
      closed: 'badge-gray'
    }[status] || 'badge-amber';
  }

  function appendMessage(role, content, timestamp) {
    if (!chatMessages) return;

    const el = document.createElement('div');
    el.className = `chat-message chat-${role}`;
    el.innerHTML = `
      <div class="chat-avatar">${role === 'doctor' ? '👨‍⚕️' : role === 'patient' ? '👤' : '🤖'}</div>
      <div class="chat-content">
        <div class="chat-text">${escapeHtml(content)}</div>
        <div class="chat-time">${formatDate(timestamp)}</div>
      </div>
    `;
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function downloadFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  // ── Initialize ────────────────────────────────────────────────────
  console.log('[Doctor] Starting initialization...');
  initSocket();
  await loadProfile();
  await Promise.all([loadStats(), loadNotifications(), loadConsultations()]);

  document.getElementById('doctor-prescription-btn')?.addEventListener('click', generatePrescription);

  // Set up real-time Socket.IO listeners for notifications
  if (socket) {
    socket.on('consultation_request', (data) => {
      console.log('[Doctor] New consultation request:', data);
      notifications.push(data.notification);
      renderNotifications();
      Toast.notification('New Consultation Request', data.notification.message);
      loadStats();

      // Notification sound
      try {
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        osc.connect(ctx.destination);
        osc.frequency.value = 880;
        osc.start();
        osc.stop(ctx.currentTime + 0.12);
      } catch (_) { /* silent */ }
    });
  }

  showPage('overview');
  console.log('[Doctor] Initialization complete');

  // Make functions global
  window.doctorNamespace.generatePrescription = generatePrescription;
  window.doctorNamespace.closeConsultation = closeConsultation;

});
