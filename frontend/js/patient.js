/* ═══════════════════════════════════════════════════════════════
   patient.js — Patient Dashboard Logic
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async () => {

  // Auth guard
  const user = Auth.getUser();
  if (!user || user.role !== 'patient') {
    window.location.href = '/';
    return;
  }

  // ── State ─────────────────────────────────────────────────────────
  let allDoctors         = [];
  let consultations      = [];
  let activeConsult      = null;
  let selectedLang       = 'en';
  let chatHistory        = [];

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
      { doctors: 'Find Doctors', chat: 'AI Health Assistant', history: 'My Consultations', profile: 'My Profile' }[pageId] || pageId;
  }

  navItems.forEach(item => item.addEventListener('click', () => showPage(item.dataset.page)));

  // ── Load doctors ──────────────────────────────────────────────────
  async function loadDoctors() {
    try {
      allDoctors = await api.get('/api/patient/doctors');
      populateSpecFilter();
      renderDoctors(allDoctors); // Show all doctors by default
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
        <div class="doctor-card-meta">
          <span class="meta-pill">🎓 ${doc.years_of_experience} yrs exp</span>
          <span class="meta-pill">🏥 ${doc.specialization}</span>
        </div>
        <div class="doctor-bio">${doc.bio || 'Experienced medical professional ready to assist you.'}</div>
        <div class="doctor-card-footer">
          ${nmcBadgeHTML(doc.nmc_verified)}
          <button
            class="btn btn-primary btn-sm"
            onclick="openConsultModal(${doc.user_id}, '${escapeHtml(doc.name)}', '${escapeHtml(doc.specialization)}', ${doc.is_available})"
            ${doc.is_available ? '' : 'disabled'}>
            ${doc.is_available ? '💬 Consult Now' : '🚫 Unavailable'}
          </button>
        </div>
      </div>
    `).join('');
  }

  // Filter bar
  document.getElementById('spec-filter').addEventListener('change', applyFilters);
  document.getElementById('avail-filter').addEventListener('click', function() {
    this.classList.toggle('active');
    applyFilters();
  });
  document.getElementById('search-doctors').addEventListener('input', applyFilters);
  document.getElementById('refresh-doctors').addEventListener('click', async function() {
    setLoading(this, true, '🔄 Refreshing...');
    await loadDoctors();
    setLoading(this, false, '🔄 Refresh');
    Toast.success('Doctor list refreshed!', 'Updated with latest availability');
  });

  function applyFilters() {
    const spec    = document.getElementById('spec-filter').value;
    const avOnly  = document.getElementById('avail-filter').classList.contains('active');
    const query   = document.getElementById('search-doctors').value.toLowerCase();
    const filtered = allDoctors.filter(d =>
      (!spec   || d.specialization === spec) &&
      (!avOnly || d.is_available) &&
      (!query  || d.name.toLowerCase().includes(query) || d.specialization.toLowerCase().includes(query))
    );
    renderDoctors(filtered);
  }

  // ── Consultation request modal ────────────────────────────────────
  window.openConsultModal = (doctorId, doctorName, spec, available) => {
    if (!available) { Toast.warning('Doctor unavailable', 'This doctor is currently not accepting consultations'); return; }
    document.getElementById('modal-doctor-name').textContent = doctorName;
    document.getElementById('modal-doctor-spec').textContent = spec;
    document.getElementById('confirm-consult-btn').dataset.doctorId = doctorId;
    consultModal.classList.add('active');
  };

  document.getElementById('close-consult-modal').addEventListener('click', () => consultModal.classList.remove('active'));
  consultModal.addEventListener('click', e => { if (e.target === e.currentTarget) consultModal.classList.remove('active'); });

  document.getElementById('confirm-consult-btn').addEventListener('click', async function() {
    const doctorId = parseInt(this.dataset.doctorId);
    const lang     = document.getElementById('modal-lang').value;
    setLoading(this, true, 'Requesting...');
    try {
      const res = await api.post('/api/patient/consult', {
        doctor_id: doctorId,
        language:  lang
      });
      activeConsult      = res.consultation;
      selectedLang       = lang;
      chatHistory        = [];

      consultModal.classList.remove('active');
      Toast.success('Consultation requested!', 'The doctor has been notified.');

      // Pre-load welcome message in chat
      chatMessages.innerHTML = '';
      appendMessage('ai', res.welcome_message, new Date().toISOString());

      await loadConsultations();
      showPage('chat');
    } catch (e) {
      Toast.error('Request failed', e.message);
    } finally {
      setLoading(this, false, '✅ Start Consultation');
    }
  });

  // ── Chat ──────────────────────────────────────────────────────────
  // Language selector
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedLang = btn.dataset.lang;
    });
  });

  chatSendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    if (!activeConsult) {
      Toast.warning('No active consultation', 'Please start a consultation with a doctor first.');
      showPage('doctors');
      return;
    }

    chatInput.value = '';
    chatSendBtn.disabled = true;

    // Show patient message
    appendMessage('patient', text, new Date().toISOString());
    chatHistory.push({ role: 'user', parts: [text] });

    // Show typing indicator
    const typingEl = appendTyping();

    try {
      const res = await api.post(`/api/patient/consultations/${activeConsult.id}/chat`, {
        message: text
      });
      typingEl.remove();
      appendMessage('ai', res.ai_response.content, res.ai_response.created_at);
      chatHistory.push({ role: 'model', parts: [res.ai_response.content] });
    } catch (e) {
      typingEl.remove();
      Toast.error('AI error', e.message);
      appendMessage('ai', '⚠️ Sorry, I encountered an error. Please try again.', new Date().toISOString());
    } finally {
      chatSendBtn.disabled = false;
      chatInput.focus();
    }
  }

  function appendMessage(role, content, timestamp) {
    const isPatient = role === 'patient';
    const div = document.createElement('div');
    div.className = `chat-message ${isPatient ? 'patient' : 'ai'}`;
    div.innerHTML = `
      <div class="msg-avatar">${isPatient ? getInitials(user.name) : '🤖'}</div>
      <div>
        <div class="msg-bubble">${escapeHtml(content).replace(/\n/g, '<br>')}</div>
        <span class="msg-time">${timeAgo(timestamp)}</span>
      </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
  }

  function appendTyping() {
    const div = document.createElement('div');
    div.className = 'chat-message ai typing-indicator';
    div.innerHTML = `
      <div class="msg-avatar">🤖</div>
      <div class="typing-dots"><span></span><span></span><span></span></div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
  }

  // Generate report button
  document.getElementById('gen-report-btn')?.addEventListener('click', async () => {
    if (!activeConsult) { Toast.warning('No consultation', 'Start a consultation first'); return; }
    const btn = document.getElementById('gen-report-btn');
    setLoading(btn, true, 'Generating...');
    try {
      const res = await api.post(`/api/patient/consultations/${activeConsult.id}/report`, {});
      Toast.success('Report generated!', 'Your consultation report is ready');
      await loadConsultations();

      // Show report in modal
      document.getElementById('history-report-content').textContent = res.report;
      document.getElementById('history-report-modal').classList.add('active');
    } catch (e) {
      Toast.error('Report failed', e.message);
    } finally {
      setLoading(btn, false, '📄 Generate Report');
    }
  });

  // ── Consultation history ──────────────────────────────────────────
  async function loadConsultations() {
    try {
      consultations = await api.get('/api/patient/consultations');
      renderHistory();
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
        <p>Start your first consultation with one of our doctors</p>
      </div>`;
      return;
    }
    list.innerHTML = consultations.map(c => `
      <div class="history-card" onclick="resumeConsult(${c.id}, '${c.status}')">
        <div class="history-icon">🏥</div>
        <div class="history-info">
          <div class="history-doctor">Dr. ${c.doctor_name}</div>
          <div class="history-meta">
            ${formatDate(c.created_at)} &nbsp;·&nbsp; ${langLabel(c.language)}
            &nbsp;·&nbsp; <span class="badge ${statusBadge(c.status)}">${c.status}</span>
          </div>
          <div class="history-preview">${c.report_text || 'Consultation in progress...'}</div>
        </div>
        ${c.report_text ? `<button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();showHistoryReport('${escapeHtml(c.report_text)}')">📄 Report</button>` : ''}
      </div>
    `).join('');
  }

  window.resumeConsult = async (consultId, status) => {
    const c = consultations.find(x => x.id === consultId);
    if (!c) return;
    activeConsult = c;
    selectedLang  = c.language;

    // Load messages
    chatMessages.innerHTML = '';
    try {
      const msgs = await api.get(`/api/patient/consultations/${consultId}/messages`);
      msgs.forEach(m => appendMessage(m.sender_role, m.content, m.created_at));
    } catch (e) { Toast.error('Failed to load chat', e.message); }

    showPage('chat');
  };

  let currentReportText = '';

  window.showHistoryReport = (text) => {
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
  document.getElementById('history-report-modal')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) e.currentTarget.classList.remove('active');
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
  document.getElementById('logout-btn').addEventListener('click', () => {
    Auth.clear();
    window.location.href = '/';
  });

  // ── Helpers ───────────────────────────────────────────────────────
  function statusBadge(status) {
    return { completed: 'badge-green', pending: 'badge-amber', active: 'badge-cyan' }[status] || 'badge-amber';
  }

  function setLoading(btn, loading, label) {
    btn.disabled = loading;
    btn.innerHTML = loading ? '<span class="spinner"></span> ' + label : label;
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, s =>
      ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[s]));
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

  // ── Init ──────────────────────────────────────────────────────────
  await Promise.all([loadDoctors(), loadConsultations()]);
  showPage('doctors');
});

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, s =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[s]));
}
