/* ═══════════════════════════════════════════════════════════════
   api.js — Centralised API wrapper + JWT handling
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:5000';

// ── Token helpers ────────────────────────────────────────────────
const Auth = {
  getToken:  ()      => localStorage.getItem('medi_token'),
  getUser:   ()      => JSON.parse(localStorage.getItem('medi_user') || 'null'),
  setToken:  (t)     => localStorage.setItem('medi_token', t),
  setUser:   (u)     => localStorage.setItem('medi_user', JSON.stringify(u)),
  clear:     ()      => { localStorage.removeItem('medi_token'); localStorage.removeItem('medi_user'); },
  isLoggedIn:()      => !!localStorage.getItem('medi_token'),
};

// ── Core fetch wrapper ───────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = Auth.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    Auth.clear();
    window.location.href = '/';
    return null;
  }

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

const api = {
  get:    (path)         => apiFetch(path, { method: 'GET' }),
  post:   (path, body)   => apiFetch(path, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (path, body)   => apiFetch(path, { method: 'PUT',    body: JSON.stringify(body) }),
  delete: (path)         => apiFetch(path, { method: 'DELETE' }),
};

// ── Toast system ─────────────────────────────────────────────────
const Toast = (() => {
  let container;

  function init() {
    if (document.getElementById('toast-container')) return;
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  function show(type, title, msg, duration = 4000) {
    init();
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️', notification: '🔔' };
    const el = document.createElement('div');
    el.className = `toast toast-${type === 'notification' ? 'info' : type}`;
    el.innerHTML = `
      <span class="toast-icon">${icons[type] || '📢'}</span>
      <div class="toast-body">
        <div class="toast-title">${title}</div>
        ${msg ? `<div class="toast-msg">${msg}</div>` : ''}
      </div>
    `;
    container.appendChild(el);
    setTimeout(() => {
      el.style.animation = 'slideOut 0.3s ease forwards';
      setTimeout(() => el.remove(), 300);
    }, duration);
  }

  return { success: (t,m,d) => show('success',t,m,d),
           error:   (t,m,d) => show('error',  t,m,d),
           info:    (t,m,d) => show('info',   t,m,d),
           warning: (t,m,d) => show('warning',t,m,d),
           notification: (t,m) => show('notification',t,m,6000) };
})();

// ── Time formatting ───────────────────────────────────────────────
function timeAgo(isoStr) {
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs}h ago`;
  return new Date(isoStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function formatDate(isoStr) {
  return new Date(isoStr).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
}

// ── Avatar initials ───────────────────────────────────────────────
function getInitials(name = '') {
  return name.split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
}

// ── NMC badge HTML ────────────────────────────────────────────────
function nmcBadgeHTML(verified) {
  if (!verified) return '';
  return `<span class="nmc-badge">
    <svg viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 1L7.5 4.5L11 5L8.5 7.5L9 11L6 9.5L3 11L3.5 7.5L1 5L4.5 4.5L6 1Z"
            fill="currentColor"/>
    </svg>NMC Verified</span>`;
}

// ── Language label ────────────────────────────────────────────────
function langLabel(code) {
  return { en: '🇬🇧 English', hi: '🇮🇳 Hindi', kn: '🌟 Kannada' }[code] || code;
}
