/* ============================================================
   provider.js — Provider Dashboard Logic
   Handles login/register, dashboard stats, job board, history
   ============================================================ */

const API = 'https://local-service-rvpo.onrender.com/api';

let provider = null;
let activeJobId = null;
let timerHandle = null;
let countdown = 10;
let registerLocation = { latitude: null, longitude: null };
const CIRCUMFERENCE = 2 * Math.PI * 17;

function showToast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span class="toast-icon">${icons[type] || '✓'}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(40px)';
    el.style.transition = 'all .3s ease';
    setTimeout(() => el.remove(), 300);
  }, 4000);
}

function setButtonState(id, loading, text) {
  const btn = document.getElementById(id);
  if (!btn) return;
  if (!btn.dataset.label) btn.dataset.label = btn.textContent.trim();
  btn.disabled = loading;
  if (loading) {
    btn.classList.add('btn-loading');
    btn.textContent = text || 'Loading…';
  } else {
    btn.classList.remove('btn-loading');
    btn.textContent = btn.dataset.label;
  }
}

function formatCurrency(amount) {
  return `₹${Number(amount || 0).toFixed(0)}`;
}

function formatSlot(date, time) {
  if (!date && !time) return '—';
  const parsed = new Date(`${date || ''}T${time || '00:00'}`);
  if (Number.isNaN(parsed.getTime())) return `${date || ''} ${time || ''}`.trim();
  return `${parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} · ${parsed.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}`;
}

/* ── Location Capture ─────────────────────────────────────── */
function captureProviderLocation(target) {
  const statusId = 'register-location-status';
  const status = document.getElementById(statusId);
  if (!navigator.geolocation) {
    if (status) status.textContent = 'Geolocation is not available in this browser.';
    showToast('Geolocation is not available.', 'error');
    return;
  }

  if (status) status.textContent = 'Fetching your current location...';
  navigator.geolocation.getCurrentPosition(
    position => {
      registerLocation.latitude = position.coords.latitude;
      registerLocation.longitude = position.coords.longitude;
      if (status) status.textContent = `📍 ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
      showToast('Location detected successfully.');
    },
    () => {
      if (status) status.textContent = 'Location denied. Enter address manually.';
      showToast('Location access was denied.', 'info');
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

/* ── Photo Upload ─────────────────────────────────────────── */
async function uploadPhoto(fileInput) {
  if (!fileInput || !fileInput.files || !fileInput.files[0]) return '';
  // Limit to 5MB
  if (fileInput.files[0].size > 5 * 1024 * 1024) {
    showToast('Image exceeds 5MB limit. Using no photo.', 'info');
    return '';
  }
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  try {
    const res = await fetch(`${API}/upload`, { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) return data.url;
    showToast(data.message || 'Photo upload failed.', 'error');
  } catch {
    showToast('Could not upload photo.', 'error');
  }
  return '';
}

/* ── Tab Switching ─────────────────────────────────────────── */
function switchProviderTab(tab) {
  document.querySelectorAll('#provider-auth .tab').forEach((button, index) => {
    const active = (tab === 'login' && index === 0) || (tab === 'register' && index === 1);
    button.classList.toggle('active', active);
  });
  document.getElementById('ppanel-login').classList.toggle('active', tab === 'login');
  document.getElementById('ppanel-register').classList.toggle('active', tab === 'register');
}

/* ── Show Dashboard ───────────────────────────────────────── */
function showProviderDashboard(current) {
  document.getElementById('provider-auth').style.display = 'none';
  document.getElementById('provider-dashboard').style.display = 'block';

  const avatarContent = current.profile_photo
    ? `<img src="${API.replace('/api','')}${current.profile_photo}" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`
    : current.name[0].toUpperCase();

  document.getElementById('nav-right').innerHTML = `
    <div class="user-chip">
      <div class="user-avatar" id="prov-avatar" style="overflow:hidden">${avatarContent}</div>
      <div class="avail-badge ${current.availability === 'BUSY' ? 'busy' : 'available'}" id="avail-badge">
        <span class="avail-dot" id="avail-dot"></span>
        <span id="avail-label">${current.availability || 'AVAILABLE'}</span>
      </div>
      <span class="user-name" id="prov-name">${current.name}</span>
      <button class="logout-btn" onclick="logout()">Sign out</button>
    </div>`;
}

function logout() {
  clearInterval(timerHandle);
  localStorage.removeItem('lses_provider');
  location.href = 'provider.html';
}

/* ── Login ─────────────────────────────────────────────────── */
async function doProviderLogin() {
  const email = document.getElementById('p-login-email').value.trim();
  const password = document.getElementById('p-login-password').value;
  if (!email || !password) { showToast('Please fill all login fields.', 'error'); return; }

  setButtonState('btn-p-login', true, 'Signing in…');
  try {
    const res = await fetch(`${API}/provider/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    let data;
    try { data = await res.json(); }
    catch { throw new Error('Invalid server response.'); }
    if (!data.success) { showToast(data.message || 'Login failed.', 'error'); return; }

    provider = data.provider;
    localStorage.setItem('lses_provider', JSON.stringify(provider));
    showProviderDashboard(provider);
    initDashboard();
    showToast(`Welcome back, ${provider.name}.`);
  } catch {
    showToast('Could not connect to the backend server.', 'error');
  } finally {
    setButtonState('btn-p-login', false);
  }
}

/* ── Register ─────────────────────────────────────────────── */
async function doProviderRegister() {
  const name = document.getElementById('p-reg-name').value.trim();
  const phone = document.getElementById('p-reg-phone').value.trim();
  const email = document.getElementById('p-reg-email').value.trim();
  const service = document.getElementById('p-reg-service').value;
  const charge = document.getElementById('p-reg-charge').value.trim();
  const chargeType = document.getElementById('p-reg-charge-type').value;
  const experience = document.getElementById('p-reg-experience').value.trim();
  const address = document.getElementById('p-reg-address').value.trim();
  const pass = document.getElementById('p-reg-password').value;

  if (!name || !phone || !email || !service || !address || !pass) {
    showToast('Please fill all required fields.', 'error');
    return;
  }

  setButtonState('btn-p-register', true, 'Creating account...');
  try {
    // Upload photo if selected
    const photoUrl = await uploadPhoto(document.getElementById('p-reg-photo'));

    const res = await fetch(`${API}/provider/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name, phone, email,
        service_type: service,
        password: pass,
        base_charge: charge || undefined,
        charge_type: chargeType,
        experience,
        address,
        latitude: registerLocation.latitude,
        longitude: registerLocation.longitude,
        profile_photo: photoUrl,
      })
    });
    const data = await res.json();
    if (!data.success) { showToast(data.message, 'error'); return; }

    showToast('Provider account created! Sign in to continue.');
    document.getElementById('p-login-email').value = email;
    switchProviderTab('login');
  } catch {
    showToast('Could not register provider right now.', 'error');
  } finally {
    setButtonState('btn-p-register', false);
  }
}

/* ── Availability ─────────────────────────────────────────── */
function setAvailability(status) {
  if (!provider) return;
  provider.availability = status;
  const badge = document.getElementById('avail-badge');
  const label = document.getElementById('avail-label');
  if (!badge || !label) return;
  badge.className = `avail-badge ${status === 'BUSY' ? 'busy' : 'available'}`;
  label.textContent = status;
}

/* ── Dashboard Init ───────────────────────────────────────── */
function initDashboard() {
  const raw = localStorage.getItem('lses_provider');
  if (!raw) return;
  provider = JSON.parse(raw);
  showProviderDashboard(provider);
  refreshAll();
  startCountdown();
}

function startCountdown() {
  clearInterval(timerHandle);
  countdown = 10;
  updateCountdownDisplay();
  timerHandle = setInterval(() => {
    countdown -= 1;
    updateCountdownDisplay();
    if (countdown <= 0) refreshAll();
  }, 1000);
}

function updateCountdownDisplay() {
  const counter = document.getElementById('countdown');
  if (counter) counter.textContent = countdown;

  const ring = document.getElementById('countdown-ring');
  if (ring) {
    const offset = CIRCUMFERENCE * (1 - countdown / 10);
    ring.setAttribute('stroke-dashoffset', offset);
  }

  const bar = document.getElementById('refresh-bar-fill');
  if (bar) bar.style.width = `${countdown / 10 * 100}%`;
}

async function refreshAll() {
  await Promise.all([fetchStats(), fetchJobs(), fetchHistory()]);
  countdown = 10;
  updateCountdownDisplay();
}

/* ── Stats ─────────────────────────────────────────────────── */
async function fetchStats() {
  try {
    const res = await fetch(`${API}/provider/stats/${provider.id}`);
    const data = await res.json();
    if (!data.success) return;

    const stats = data.stats;
    document.getElementById('stat-completed').textContent = stats.completed_jobs;
    document.getElementById('stat-active').textContent = stats.active_jobs;
    document.getElementById('stat-pending').textContent = stats.pending_jobs;
    document.getElementById('stat-service').textContent = stats.provider.service_type || '—';

    provider = { ...provider, ...stats.provider };
    localStorage.setItem('lses_provider', JSON.stringify(provider));

    if (stats.active_job) {
      activeJobId = stats.active_job.id;
      renderActiveJob(stats.active_job);
      document.getElementById('active-job-section').style.display = 'block';
      setAvailability('BUSY');
    } else {
      activeJobId = null;
      document.getElementById('active-job-section').style.display = 'none';
      setAvailability('AVAILABLE');
    }
  } catch (error) {
    console.error(error);
  }
}

/* ── Active Job Rendering ─────────────────────────────────── */
function renderActiveJob(job) {
  document.getElementById('aj-id').textContent = `#${job.id}`;
  document.getElementById('aj-slot').textContent = formatSlot(job.scheduled_date, job.scheduled_time);
  document.getElementById('aj-name').textContent = job.customer_name;
  document.getElementById('aj-phone').textContent = job.phone;
  document.getElementById('aj-service').textContent = job.service_type || '—';
  document.getElementById('aj-payment').textContent = job.payment_status || '—';
  document.getElementById('aj-total').textContent = formatCurrency(job.total_amount);
  document.getElementById('aj-address').textContent = job.address || '—';
  document.getElementById('aj-desc').textContent = job.description || '—';

  const map = document.getElementById('active-job-map');
  if (job.map_url) {
    map.src = job.map_url;
    map.style.display = 'block';
  } else {
    map.removeAttribute('src');
    map.style.display = 'none';
  }
}

/* ── Job Board ─────────────────────────────────────────────── */
async function fetchJobs() {
  try {
    const res = await fetch(`${API}/requests?provider_id=${provider.id}`);
    const data = await res.json();
    if (!data.success) return;

    const jobs = data.requests || [];
    document.getElementById('jobs-count').textContent = `${jobs.length} booking${jobs.length !== 1 ? 's' : ''}`;
    renderJobs(jobs);
  } catch (error) {
    console.error(error);
  }
}

function renderJobs(jobs) {
  const grid = document.getElementById('jobs-grid');
  if (!jobs.length) {
    grid.innerHTML = `
      <div class="glass glass-pad empty-state">
        <div class="empty-title">No new paid bookings right now</div>
        <div style="color:var(--text-3)">Customers will appear here after they complete payment.</div>
      </div>`;
    return;
  }

  grid.innerHTML = jobs.map(job => `
    <article class="glass glass-pad booking-job-card">
      <div class="job-header">
        <span class="job-id">Booking #${job.id}</span>
        <span class="job-service-chip">${job.service_type}</span>
      </div>
      <div class="job-name">${job.customer_name}</div>
      <div class="provider-detail-line">📞 ${job.phone}</div>
      <div class="provider-detail-line">📅 ${formatSlot(job.scheduled_date, job.scheduled_time)}</div>
      <div class="provider-detail-line">💰 ${formatCurrency(job.total_amount)} · Payment: ${job.payment_status}</div>
      <div class="provider-detail-line">📍 ${job.address || 'Address unavailable'}</div>
      <div class="job-desc">${job.description || '—'}</div>
      ${job.map_url ? `<iframe class="booking-map compact-map" title="Customer map" loading="lazy" src="${job.map_url}"></iframe>` : ''}
      <div class="job-footer">
        <span class="job-time">Created ${job.created_at}</span>
        <div style="display:flex;gap:8px">
          <button class="btn btn-success btn-sm" onclick="acceptJob(${job.id}, this)">✅ Accept</button>
          <button class="btn btn-danger btn-sm" onclick="rejectJob(${job.id}, this)" style="font-size:12px">✕ Reject</button>
        </div>
      </div>
    </article>
  `).join('');
}

/* ── Accept Job ───────────────────────────────────────────── */
async function acceptJob(jobId, btn) {
  if (provider.availability === 'BUSY') {
    showToast('Finish the active booking before accepting a new one.', 'error');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Accepting...';
  try {
    const res = await fetch(`${API}/request/${jobId}/accept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_id: provider.id })
    });
    const data = await res.json();
    if (!data.success) {
      showToast(data.message, 'error');
      btn.disabled = false;
      btn.textContent = '✅ Accept';
      return;
    }
    showToast('Booking accepted successfully!');
    refreshAll();
  } catch {
    showToast('Could not accept the booking.', 'error');
    btn.disabled = false;
    btn.textContent = '✅ Accept';
  }
}

/* ── Reject Job (UI-only feedback) ────────────────────────── */
function rejectJob(jobId, btn) {
  btn.disabled = true;
  btn.textContent = 'Rejected';
  btn.closest('.booking-job-card').style.opacity = '0.4';
  showToast('Booking declined.', 'info');
}

/* ── Complete Job ─────────────────────────────────────────── */
async function completeJob() {
  if (!activeJobId) return;

  setButtonState('btn-complete', true, 'Completing...');
  try {
    const res = await fetch(`${API}/request/${activeJobId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_id: provider.id })
    });
    const data = await res.json();
    if (!data.success) {
      showToast(data.message, 'error');
      return;
    }
    showToast('Booking marked as completed! 🎉');
    refreshAll();
  } catch {
    showToast('Could not complete the booking.', 'error');
  } finally {
    setButtonState('btn-complete', false);
  }
}

/* ── History ──────────────────────────────────────────────── */
async function fetchHistory() {
  const target = document.getElementById('provider-history');
  if (!target) return;
  try {
    const res = await fetch(`${API}/bookings/provider/${provider.id}`);
    const data = await res.json();
    if (!data.success) {
      target.innerHTML = `<div class="empty-state-inline">${data.message}</div>`;
      return;
    }
    renderHistory(data.bookings || []);
  } catch {
    target.innerHTML = '<div class="empty-state-inline">Could not load booking history.</div>';
  }
}

function renderHistory(bookings) {
  const target = document.getElementById('provider-history');
  if (!bookings.length) {
    target.innerHTML = '<div class="empty-state-inline">No received bookings yet.</div>';
    return;
  }

  target.innerHTML = bookings.map(booking => {
    const statusClass = booking.status === 'COMPLETED' ? 'badge-completed' : booking.status === 'ACCEPTED' ? 'badge-assigned' : 'badge-pending';
    return `
    <article class="history-card">
      <div class="history-card-head">
        <div>
          <div class="history-card-title">#${booking.id} · ${booking.customer_name}</div>
          <div class="history-card-sub">${booking.service_type} · ${formatSlot(booking.scheduled_date, booking.scheduled_time)}</div>
        </div>
        <div class="history-status-stack">
          <span class="badge ${statusClass}"><span class="badge-dot"></span>${booking.status}</span>
          <span class="mini-badge">${booking.payment_status_label || booking.payment_status}</span>
        </div>
      </div>
      <div class="provider-detail-line">📞 ${booking.phone}</div>
      <div class="provider-detail-line">📍 ${booking.address || 'No address saved'}</div>
      <div class="provider-detail-line">💰 ${formatCurrency(booking.total_amount)}</div>
      <div class="provider-detail-line">${booking.description || '—'}</div>
    </article>`;
  }).join('');
}

/* ── Init on page load ────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const raw = localStorage.getItem('lses_provider');
  if (raw) {
    provider = JSON.parse(raw);
    showProviderDashboard(provider);
    initDashboard();
  }
});
