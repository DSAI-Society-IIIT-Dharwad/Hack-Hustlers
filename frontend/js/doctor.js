/* ═══════════════════════════════════════════════════════════════
   doctor.js — Doctor Dashboard Logic
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async () => {

  // Auth guard
  const user = Auth.getUser();
  if (!user || user.role !== 'doctor') {
    window.location.href = '/';
    return;
  }

  // ── State ─────────────────────────────────────────────────────────
  let profile       = null;
  let notifications = [];
  let consultations = [];
  let socket        = null;

  // ── DOM refs ──────────────────────────────────────────────────────
  const navItems      = document.querySelectorAll('.nav-item[data-page]');
  const pages         = document.querySelectorAll('.page-content');
  const availToggle   = document.getElementById('avail-toggle');
  const notifBadgeNav = document.getElementById('notif-badge-nav');

  // ── Page navigation ───────────────────────────────────────────────
  function showPage(pageId) {
    pages.forEach(p => p.classList.add('hidden'));
    navItems.forEach(n => n.classList.remove('active'));
    const target = document.getElementById(`page-${pageId}`);
    if (target) target.classList.remove('hidden');
    document.querySelector(`.nav-item[data-page="${pageId}"]`)?.classList.add('active');
    document.getElementById('topbar-title').textContent =
      { overview: 'Overview', notifications: 'Notifications', history: 'Consultation History', profile: 'My Profile' }[pageId] || pageId;
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const page = item.dataset.page;
      showPage(page);
      if (page === 'notifications') markAllRead();
    });
  });

  // ── Load doctor profile ───────────────────────────────────────────
  async function loadProfile() {
    try {
      profile = await api.get('/api/doctor/profile');
      renderProfileCard();
      updateAvailabilityUI(profile.doctor?.is_available ?? true);

      // Sidebar user info
      document.getElementById('sidebar-name').textContent  = profile.name;
      document.getElementById('sidebar-email').textContent = profile.email;
      document.getElementById('sidebar-avatar').textContent= getInitials(profile.name);
      document.getElementById('topbar-user').textContent   = profile.name;
    } catch (e) {
      Toast.error('Failed to load profile', e.message);
    }
  }

  // ── Load stats ────────────────────────────────────────────────────
  async function loadStats() {
    try {
      const stats = await api.get('/api/doctor/stats');
      document.getElementById('stat-total').textContent    = stats.total_consultations;
      document.getElementById('stat-completed').textContent = stats.completed;
      document.getElementById('stat-pending').textContent   = stats.pending;
      document.getElementById('stat-unread').textContent    = stats.unread_notifications;
    } catch (e) { /* silent */ }
  }

  // ── Availability toggle ───────────────────────────────────────────
  function updateAvailabilityUI(available) {
    if (available) {
      availToggle.className = 'availability-toggle available';
      availToggle.innerHTML = `<span class="dot dot-green"></span><span class="toggle-label">Available</span>`;
    } else {
      availToggle.className = 'availability-toggle unavailable';
      availToggle.innerHTML = `<span class="dot dot-red"></span><span class="toggle-label">Unavailable</span>`;
    }
  }

  availToggle.addEventListener('click', async () => {
    try {
      const current = profile?.doctor?.is_available ?? true;
      const res = await api.put('/api/doctor/availability', { is_available: !current });
      profile.doctor.is_available = res.is_available;
      updateAvailabilityUI(res.is_available);
      Toast.success('Availability updated', res.is_available ? 'You are now available' : 'You are now unavailable');
    } catch (e) {
      Toast.error('Update failed', e.message);
    }
  });

  // ── Load notifications ────────────────────────────────────────────
  async function loadNotifications() {
    try {
      notifications = await api.get('/api/doctor/notifications');
      renderNotifications();
      const unread = notifications.filter(n => !n.is_read).length;
      if (unread > 0) {
        notifBadgeNav.textContent = unread;
        notifBadgeNav.style.display = 'inline-block';
      } else {
        notifBadgeNav.style.display = 'none';
      }
      document.getElementById('stat-unread').textContent = unread;
    } catch (e) {
      Toast.error('Failed to load notifications', e.message);
    }
  }

  function renderNotifications() {
    const list    = document.getElementById('notif-list');
    const preview = document.getElementById('overview-notif-list');

    const emptyHTML = `<div class="empty-state">
      <div class="empty-icon">🔔</div>
      <h3>No notifications yet</h3>
      <p>You'll see patient consultation requests here</p>
    </div>`;

    if (!notifications.length) {
      list.innerHTML    = emptyHTML;
      preview.innerHTML = emptyHTML;
      return;
    }

    const makeCard = (n) => `
      <div class="notif-card ${n.is_read ? 'read' : ''}">
        <div class="notif-avatar">${getInitials(n.patient_name)}</div>
        <div class="notif-content">
          <div class="notif-name">${n.patient_name}</div>
          <div class="notif-msg">${n.message}</div>
          <div class="notif-time">${timeAgo(n.created_at)}</div>
        </div>
        ${!n.is_read ? '<div class="notif-unread-dot"></div>' : ''}
      </div>
    `;

    list.innerHTML    = notifications.map(makeCard).join('');
    preview.innerHTML = notifications.slice(0, 3).map(makeCard).join('');
  }

  async function markAllRead() {
    const unread = notifications.filter(n => !n.is_read);
    if (!unread.length) { Toast.info('All caught up!', 'No unread notifications'); return; }
    await api.put('/api/doctor/notifications/mark-all-read', {});
    notifications.forEach(n => n.is_read = true);
    notifBadgeNav.style.display = 'none';
    document.getElementById('stat-unread').textContent = '0';
    renderNotifications();
    Toast.success('Done', 'All notifications marked as read');
  }

  document.getElementById('mark-all-btn').addEventListener('click', markAllRead);

  // ── Load consultations ────────────────────────────────────────────
  async function loadConsultations() {
    try {
      consultations = await api.get('/api/doctor/consultations');
      renderConsultations();
    } catch (e) {
      Toast.error('Failed to load consultations', e.message);
    }
  }

  function renderConsultations() {
    const tbody   = document.getElementById('consult-table-body');
    const preview = document.getElementById('consult-preview-body');

    const emptyHTML = `<div class="empty-state" style="padding:40px">
      <div class="empty-icon">📋</div>
      <h3>No consultations yet</h3>
      <p>Your consultation history will appear here</p>
    </div>`;

    if (!consultations.length) {
      tbody.innerHTML   = emptyHTML;
      preview.innerHTML = emptyHTML;
      document.getElementById('history-count').textContent = '0 records';
      return;
    }

    document.getElementById('history-count').textContent = `${consultations.length} record${consultations.length !== 1 ? 's' : ''}`;

    const makeRow = (c) => `
      <div class="consult-row" onclick="viewReport(${c.id})">
        <div>
          <div class="consult-patient-name">${c.patient_name}</div>
          <div class="consult-patient-info">Patient #${c.patient_id}</div>
        </div>
        <div class="consult-date">${formatDate(c.created_at)}</div>
        <div><span class="badge ${statusBadge(c.status)}">${c.status}</span></div>
        <div class="consult-lang col-lang">${langLabel(c.language)}</div>
        <div class="col-action-label">
          <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();viewReport(${c.id})">View</button>
        </div>
      </div>
    `;

    tbody.innerHTML   = consultations.map(makeRow).join('');
    preview.innerHTML = consultations.slice(0, 5).map(makeRow).join('');
  }

  function statusBadge(status) {
    return { completed: 'badge-green', pending: 'badge-amber', active: 'badge-cyan' }[status] || 'badge-amber';
  }

  // ── View report modal ─────────────────────────────────────────────
  window.viewReport = async (consultId) => {
    const c = consultations.find(x => x.id === consultId);
    if (!c) return;

    const modal   = document.getElementById('report-modal');
    const content = document.getElementById('report-content');
    document.getElementById('report-patient').textContent = c.patient_name;
    document.getElementById('report-date').textContent    = formatDate(c.created_at);
    document.getElementById('report-status').innerHTML    = `<span class="badge ${statusBadge(c.status)}">${c.status}</span>`;

    content.textContent = c.report_text || '⏳ No report generated yet for this consultation.';
    modal.classList.add('active');
  };

  document.getElementById('download-report-btn')?.addEventListener('click', () => {
    const content = document.getElementById('report-content').textContent || '';
    if (!content) return;
    downloadReport(content, `MediConsult_Report_${new Date().toISOString().slice(0,10)}.txt`);
  });

  document.getElementById('print-report-btn')?.addEventListener('click', () => {
    const content = document.getElementById('report-content').textContent || '';
    if (!content) return;
    printReport(content);
  });

  document.getElementById('report-modal-close').addEventListener('click', () => {
    document.getElementById('report-modal').classList.remove('active');
  });
  document.getElementById('report-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) e.currentTarget.classList.remove('active');
  });

  // ── Render profile card ───────────────────────────────────────────
  function renderProfileCard() {
    if (!profile) return;
    const d = profile.doctor || {};
    document.getElementById('profile-avatar').textContent = getInitials(profile.name);
    document.getElementById('profile-name').textContent   = profile.name;
    document.getElementById('profile-spec').textContent   = d.specialization || '';
    document.getElementById('profile-years').textContent  = `${d.years_of_experience || 0} years experience`;
    document.getElementById('profile-nmc-status').innerHTML = d.nmc_verified
      ? nmcBadgeHTML(true) : '<span class="badge badge-amber">⏳ Pending Verification</span>';
    document.getElementById('profile-email').textContent  = profile.email;
    document.getElementById('profile-nmc-id').textContent = d.nmc_id || 'Not provided';
    document.getElementById('profile-bio').textContent    = d.bio || 'No bio added.';
  }

  // ── WebSocket — real-time notifications ───────────────────────────
  function initSocket() {
    socket = io('http://localhost:5000', { transports: ['websocket'] });

    socket.on('connect', () => {
      socket.emit('join_doctor_room', { doctor_id: user.id });
      console.log('[Socket] Connected to MediConsult server');
    });

    socket.on('new_notification', (notif) => {
      notifications.unshift(notif);
      renderNotifications();

      // Update badge
      const unread = notifications.filter(n => !n.is_read).length;
      notifBadgeNav.textContent = unread;
      notifBadgeNav.style.display = 'inline-block';
      document.getElementById('stat-unread').textContent = unread;

      // Show toast
      Toast.notification('New Consultation Request', notif.message);

      // Notification sound (beep)
      try {
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        osc.connect(ctx.destination);
        osc.frequency.value = 880;
        osc.start();
        osc.stop(ctx.currentTime + 0.12);
      } catch (_) { /* silent */ }
    });

    socket.on('disconnect', () => console.log('[Socket] Disconnected'));
  }

  // ── Logout ────────────────────────────────────────────────────────
  document.getElementById('logout-btn').addEventListener('click', () => {
    Auth.clear();
    window.location.href = '/';
  });

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

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, s =>
      ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[s]));
  }

  // ── Init ──────────────────────────────────────────────────────────
  await loadProfile();
  await Promise.all([loadStats(), loadNotifications(), loadConsultations()]);
  initSocket();
  showPage('overview');

  // Poll stats every 30s as backup
  setInterval(loadStats, 30000);
});
