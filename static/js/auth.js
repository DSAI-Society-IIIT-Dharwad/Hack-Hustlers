/**
 * Auth Module — Login, Register, Role navigation
 */

document.addEventListener('DOMContentLoaded', () => {
    // If already logged in, redirect
    const auth = getAuth();
    if (auth) {
        window.location.href = auth.user.role === 'doctor' ? '/doctor' : '/patient';
        return;
    }

    // Section toggle
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-section').classList.add('hidden');
        document.getElementById('register-section').classList.remove('hidden');
    });
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-section').classList.add('hidden');
        document.getElementById('login-section').classList.remove('hidden');
    });

    // Role toggle
    let selectedRole = 'patient';
    document.querySelectorAll('.role-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            selectedRole = btn.dataset.role;
            document.querySelectorAll('.role-toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelector('.patient-only').style.display = selectedRole === 'patient' ? '' : 'none';
            document.querySelector('.doctor-only').style.display  = selectedRole === 'doctor'  ? '' : 'none';
        });
    });

    // ── LOGIN ──
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('login-submit-btn');
        const errEl = document.getElementById('login-error');
        errEl.style.display = 'none';
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Signing in...';

        try {
            const result = await apiCall('/auth/login', 'POST', {
                email:    document.getElementById('login-email').value.trim(),
                password: document.getElementById('login-password').value
            });

            if (result && result.token) {
                saveAuth(result.token, result.user);
                showToast(`Welcome, ${result.user.name}! 👋`, 'success');
                setTimeout(() => {
                    window.location.href = result.user.role === 'doctor' ? '/doctor' : '/patient';
                }, 600);
            } else {
                throw new Error(result?.error || 'Login failed');
            }
        } catch (err) {
            errEl.textContent = err.message || 'Invalid credentials';
            errEl.style.display = 'block';
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
        }
    });

    // ── REGISTER ──
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errEl = document.getElementById('register-error');
        errEl.style.display = 'none';

        const password = document.getElementById('reg-password').value;
        const confirm  = document.getElementById('reg-confirm-password').value;
        if (password !== confirm) {
            errEl.textContent = 'Passwords do not match';
            errEl.style.display = 'block';
            return;
        }

        const payload = {
            name:     document.getElementById('reg-name').value.trim(),
            email:    document.getElementById('reg-email').value.trim(),
            password,
            role:     selectedRole
        };

        if (selectedRole === 'doctor') {
            payload.specialization = document.getElementById('reg-specialization').value;
            payload.experience_years = parseInt(document.getElementById('reg-experience').value) || 0;
        } else {
            payload.age         = parseInt(document.getElementById('reg-age').value) || null;
            payload.gender      = document.getElementById('reg-gender').value;
            payload.blood_group = document.getElementById('reg-blood-group').value;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Creating...';

        try {
            const result = await apiCall('/auth/register', 'POST', payload);
            if (result && result.token) {
                saveAuth(result.token, result.user);
                showToast('Account created! Welcome! 🎉', 'success');
                setTimeout(() => {
                    window.location.href = result.user.role === 'doctor' ? '/doctor' : '/patient';
                }, 600);
            } else {
                throw new Error(result?.error || 'Registration failed');
            }
        } catch (err) {
            errEl.textContent = err.message || 'Registration failed';
            errEl.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
        }
    });
});
