/* ═══════════════════════════════════════════════════════════════
   enhanced-api.js — Enhanced API wrapper with better error handling + Socket.IO
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:5000';

// ── Token helpers ────────────────────────────────────────────
const Auth = {
  getToken:  ()      => localStorage.getItem('medi_token'),
  getUser:   ()      => JSON.parse(localStorage.getItem('medi_user') || 'null'),
  setToken:  (t)     => localStorage.setItem('medi_token', t),
  setUser:   (u)     => localStorage.setItem('medi_user', JSON.stringify(u)),
  clear:     ()      => { localStorage.removeItem('medi_token'); localStorage.removeItem('medi_user'); },
  isLoggedIn:()      => !!localStorage.getItem('medi_token'),
};

// ── Core fetch wrapper with error resilience ─────────────────
async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = Auth.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      timeout: 10000
    });

    // Special handling for 401 to prevent logout on transient errors
    if (res.status === 401) {
      const errorText = await res.text();
      // Only logout if it's a clear unauthorized response
      if (errorText.includes('Unauthorized') || errorText.includes('token')) {
        console.warn('[API] Unauthorized - clearing session');
        Auth.clear();
        window.location.href = '/';
        return null;
      }
    }

    // Try to parse as JSON
    let data;
    try {
      data = await res.json();
    } catch (e) {
      // If JSON parsing fails, return a structured error
      throw new Error(`Invalid response: ${res.status}`);
    }

    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;

  } catch (error) {
    console.error(`[API] Error on ${path}:`, error.message);
    throw error;
  }
}

const api = {
  get:    (path)         => apiFetch(path, { method: 'GET' }),
  post:   (path, body)   => apiFetch(path, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (path, body)   => apiFetch(path, { method: 'PUT',    body: JSON.stringify(body) }),
  delete: (path)         => apiFetch(path, { method: 'DELETE' }),
};

// ── Socket.IO initialization ─────────────────────────────────
let socket = null;

function initSocket() {
  if (socket && socket.connected) return;

  try {
    const token = Auth.getToken();
    if (!token) {
      console.warn('[Socket] No token available');
      return;
    }

    socket = io(API_BASE, {
      query: { token },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    socket.on('connect', () => {
      console.log('[Socket] Connected:', socket.id);
    });

    socket.on('error', (error) => {
      console.error('[Socket] Error:', error);
    });

    socket.on('disconnect', () => {
      console.log('[Socket] Disconnected');
    });

    socket.on('connection_response', (data) => {
      console.log('[Socket] Connection response:', data);
    });

  } catch (error) {
    console.error('[Socket] Initialization failed:', error);
  }
}

function joinConsultationRoom(consultationId) {
  if (!socket) initSocket();
  if (!socket || !socket.connected) {
    console.warn('[Socket] Not connected, cannot join room');
    return;
  }

  const token = Auth.getToken();
  socket.emit('join_consultation', {
    consultation_id: consultationId,
    token
  });

  console.log('[Socket] Joined consultation room:', consultationId);
}

function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

// ── Toast system ─────────────────────────────────────────────
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

  return {
    success: (t,m,d) => show('success',t,m,d),
    error:   (t,m,d) => show('error',  t,m,d),
    info:    (t,m,d) => show('info',   t,m,d),
    warning: (t,m,d) => show('warning',t,m,d),
    notification: (t,m) => show('notification',t,m,6000)
  };
})();

// ── Utility helpers ──────────────────────────────────────────
function getInitials(name) {
  return (name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function formatDate(dateStr) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, s =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[s]));
}

// ── Language utilities ───────────────────────────────────────
const LANGUAGES = {
  en: { name: 'English', flag: '🇬🇧' },
  hi: { name: 'हिंदी', flag: '🇮🇳' },
  kn: { name: 'ಕನ್ನಡ', flag: '🇮🇳' }
};

function langLabel(code) {
  return LANGUAGES[code]?.name || code;
}
