/* ═══════════════════════════════════════════════════════════════
   auth.js — Login / Signup page logic
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // Redirect if already logged in
  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    window.location.href = user?.role === 'doctor' ? '/doctor' : '/patient';
    return;
  }

  // ── Animated background particles ───────────────────────────────
  createParticles();

  // ── Tab switching (Login ↔ Signup) ───────────────────────────────
  const loginTab  = document.getElementById('login-tab');
  const signupTab = document.getElementById('signup-tab');
  const loginForm = document.getElementById('login-form');
  const signupForm= document.getElementById('signup-form');

  function showTab(tab) {
    if (tab === 'login') {
      loginTab.classList.add('active'); signupTab.classList.remove('active');
      loginForm.style.display  = 'flex'; signupForm.style.display = 'none';
      document.getElementById('auth-title').textContent    = 'Welcome back';
      document.getElementById('auth-subtitle').textContent = 'Sign in to your MediConsult account';
    } else {
      signupTab.classList.add('active'); loginTab.classList.remove('active');
      signupForm.style.display = 'flex'; loginForm.style.display  = 'none';
      document.getElementById('auth-title').textContent    = 'Create account';
      document.getElementById('auth-subtitle').textContent = 'Join MediConsult — your health, our priority';
    }
  }

  loginTab.addEventListener('click',  () => showTab('login'));
  signupTab.addEventListener('click', () => showTab('signup'));

  // ── Role selector (signup) ───────────────────────────────────────
  const patientExtra = document.getElementById('patient-extra');
  const doctorExtra  = document.getElementById('doctor-extra');

  document.querySelectorAll('input[name="signup-role"]').forEach(radio => {
    radio.addEventListener('change', () => {
      const role = radio.value;
      if (role === 'patient') {
        patientExtra.classList.add('visible');
        doctorExtra.classList.remove('visible');
      } else {
        doctorExtra.classList.add('visible');
        patientExtra.classList.remove('visible');
      }
    });
  });

  // ── Password toggle ──────────────────────────────────────────────
  document.querySelectorAll('.password-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.previousElementSibling;
      if (input.type === 'password') { input.type = 'text'; btn.textContent = '🙈'; }
      else                           { input.type = 'password'; btn.textContent = '👁'; }
    });
  });

  // ── LOGIN ────────────────────────────────────────────────────────
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    setLoading(btn, true);

    try {
      const data = await api.post('/api/auth/login', {
        email:    document.getElementById('login-email').value.trim(),
        password: document.getElementById('login-password').value,
      });

      Auth.setToken(data.token);
      Auth.setUser(data.user);

      Toast.success('Login successful!', `Welcome back, ${data.user.name}`);
      setTimeout(() => {
        window.location.href = data.user.role === 'doctor' ? '/doctor' : '/patient';
      }, 800);

    } catch (err) {
      Toast.error('Login failed', err.message);
    } finally {
      setLoading(btn, false);
    }
  });

  // ── SIGNUP ───────────────────────────────────────────────────────
  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('signup-btn');

    const name     = document.getElementById('signup-name').value.trim();
    const email    = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirm  = document.getElementById('signup-confirm').value;
    const role     = document.querySelector('input[name="signup-role"]:checked')?.value;

    if (!role)                     { Toast.error('Role required', 'Please select Patient or Doctor'); return; }
    if (password !== confirm)      { Toast.error('Password mismatch', 'Passwords do not match'); return; }
    if (password.length < 8)       { Toast.error('Weak password', 'Password must be at least 8 characters'); return; }

    const payload = { name, email, password, role };

    if (role === 'patient') {
      payload.age         = parseInt(document.getElementById('patient-age').value) || null;
      payload.blood_group = document.getElementById('patient-blood').value || null;
    } else {
      payload.specialization      = document.getElementById('doctor-spec').value;
      payload.years_of_experience = parseInt(document.getElementById('doctor-years').value) || 0;
      payload.nmc_id              = document.getElementById('doctor-nmc').value.trim();
      payload.bio                 = document.getElementById('doctor-bio').value.trim();
    }

    setLoading(btn, true);
    try {
      const data = await api.post('/api/auth/signup', payload);
      Auth.setToken(data.token);
      Auth.setUser(data.user);
      Toast.success('Account created!', `Welcome to MediConsult, ${data.user.name}!`);
      setTimeout(() => {
        window.location.href = data.user.role === 'doctor' ? '/doctor' : '/patient';
      }, 800);
    } catch (err) {
      Toast.error('Signup failed', err.message);
    } finally {
      setLoading(btn, false);
    }
  });

  // ── Helpers ──────────────────────────────────────────────────────
  function setLoading(btn, loading) {
    btn.disabled = loading;
    btn.innerHTML = loading
      ? '<span class="spinner"></span> Please wait...'
      : btn.dataset.label;
  }

  function createParticles() {
    const bg = document.querySelector('.auth-bg');
    for (let i = 0; i < 20; i++) {
      const dot = document.createElement('div');
      dot.className = 'auth-bg-dot';
      const size = Math.random() * 4 + 2;
      const hue  = Math.random() > 0.5 ? '190' : '270';
      Object.assign(dot.style, {
        width:  size + 'px',
        height: size + 'px',
        background: `hsl(${hue}, 80%, 60%)`,
        left: Math.random() * 100 + '%',
        animationDuration: (Math.random() * 15 + 10) + 's',
        animationDelay:    (Math.random() * 10) + 's',
      });
      bg.appendChild(dot);
    }
  }
});
