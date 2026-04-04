/**
 * ═══════════════════════════════════════════════════════════════
 * Utility Module — API helpers, localStorage fallback, Toast, etc.
 * ═══════════════════════════════════════════════════════════════
 */

const API_BASE = window.location.origin;
let USE_BACKEND = true;

// ── LocalStorage Keys ──
const LS_KEYS = {
    TOKEN: 'tele_token',
    USER: 'tele_user',
    CONSULTATIONS: 'tele_consultations',
    PRESCRIPTIONS: 'tele_prescriptions',
    REPORTS: 'tele_reports'
};

// ── API Helper ──
async function apiCall(endpoint, method = 'GET', body = null) {
    const token = sessionStorage.getItem(LS_KEYS.TOKEN) || localStorage.getItem(LS_KEYS.TOKEN);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || `HTTP ${res.status}`);
        }
        return data;
    } catch (err) {
        if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
            USE_BACKEND = false;
            console.warn('⚠️ Backend unreachable, using localStorage fallback');
            return null;
        }
        throw err;
    }
}

// ── Auth Helpers ──
function saveAuth(token, user) {
    sessionStorage.setItem(LS_KEYS.TOKEN, token);
    sessionStorage.setItem(LS_KEYS.USER, JSON.stringify(user));
    localStorage.setItem(LS_KEYS.TOKEN, token);
    localStorage.setItem(LS_KEYS.USER, JSON.stringify(user));
}

function getAuth() {
    const token = sessionStorage.getItem(LS_KEYS.TOKEN) || localStorage.getItem(LS_KEYS.TOKEN);
    const userStr = sessionStorage.getItem(LS_KEYS.USER) || localStorage.getItem(LS_KEYS.USER);
    if (!token || !userStr) return null;
    try {
        return { token, user: JSON.parse(userStr) };
    } catch {
        return null;
    }
}

function clearAuth() {
    sessionStorage.removeItem(LS_KEYS.TOKEN);
    sessionStorage.removeItem(LS_KEYS.USER);
    localStorage.removeItem(LS_KEYS.TOKEN);
    localStorage.removeItem(LS_KEYS.USER);
}

function requireAuth(requiredRole = null) {
    const auth = getAuth();
    if (!auth) {
        window.location.href = '/';
        return null;
    }
    if (requiredRole && auth.user.role !== requiredRole) {
        window.location.href = auth.user.role === 'doctor' ? '/doctor' : '/patient';
        return null;
    }
    return auth;
}

// ── Toast Notifications ──
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastSlideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ── Format Helpers ──
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric'
    });
}

function formatTime(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit'
    });
}

function formatDateTime(dateStr) {
    return `${formatDate(dateStr)} ${formatTime(dateStr)}`;
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function getNowTimestamp() {
    return new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ── LocalStorage CRUD (Fallback) ──
function lsGet(key, defaultVal = []) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultVal;
    } catch {
        return defaultVal;
    }
}

function lsSet(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function lsAppend(key, item) {
    const arr = lsGet(key, []);
    arr.push(item);
    lsSet(key, arr);
    return arr;
}

// ── Debounce ──
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ── Escape HTML ──
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
