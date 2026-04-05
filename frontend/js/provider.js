/* ============================================================
   provider.js  —  Provider dashboard logic
   Used by: provider.html
   Auto-refresh every 10s, accept/complete jobs, stats
   ============================================================ */
// ✅ LOCAL DEVELOPMENT — Flask backend running on localhost
const API = 'http://localhost:5000/api';

let provider    = null;
let activeJobId = null;
let timerHandle = null;
let countdown   = 10;

/* ── TOAST ────────────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span class="toast-icon">${icons[type]||'✓'}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => { el.style.animation = 'slideIn .3s ease reverse'; setTimeout(() => el.remove(), 280); }, 4000);
}

/* ── AUTH GUARD ───────────────────────────────────────────── */
function initDashboard() {
  const raw = localStorage.getItem('lses_provider');
  if (!raw) return;   // HTML inline script handles auth + redirect
  provider = JSON.parse(raw);

  const nameEl = document.getElementById('prov-name');
  if (nameEl) nameEl.textContent = provider.name;
  document.getElementById('stat-service').textContent = provider.service_type.toUpperCase();
  const av = document.getElementById('prov-avatar');
  if (av) av.textContent = provider.name[0].toUpperCase();

  refreshAll();
  startCountdown();
}

function logout() {
  clearInterval(timerHandle);
  localStorage.removeItem('lses_provider');
  location.href = 'provider.html';
}

/* ── COUNTDOWN & AUTO REFRESH ─────────────────────────────── */
function startCountdown() {
  clearInterval(timerHandle);
  countdown = 10;
  updateCountdownDisplay();
  timerHandle = setInterval(() => {
    countdown--;
    updateCountdownDisplay();
    if (countdown <= 0) { refreshAll(); }
  }, 1000);
}

function updateCountdownDisplay() {
  const el = document.getElementById('countdown');
  if (el) el.textContent = countdown;
}

/* ── REFRESH ALL DATA ─────────────────────────────────────── */
async function refreshAll() {
  await Promise.all([ fetchStats(), fetchJobs() ]);
  countdown = 10;
  updateCountdownDisplay();
}

/* ── FETCH STATS & ACTIVE JOB ─────────────────────────────── */
async function fetchStats() {
  try {
    const res  = await fetch(`${API}/provider/stats/${provider.id}`);
    const data = await res.json();
    if (!data.success) return;

    const s = data.stats;
    document.getElementById('stat-completed').textContent = s.completed_jobs;
    document.getElementById('stat-active').textContent    = s.active_jobs;

    if (s.active_job) {
      activeJobId = s.active_job.id;
      renderActiveJob(s.active_job);
      document.getElementById('active-job-section').style.display = 'block';
      setAvailability('BUSY');
    } else {
      activeJobId = null;
      document.getElementById('active-job-section').style.display = 'none';
      setAvailability('AVAILABLE');
    }
  } catch (e) { console.error('Stats error:', e); }
}

function setAvailability(status) {
  provider.availability = status;
  const dot   = document.getElementById('avail-dot');
  const label = document.getElementById('avail-label');
  if (!dot || !label) return;
  if (status === 'BUSY') {
    dot.className   = 'avail-dot busy';
    label.className = 'avail-label busy';
    label.textContent = 'BUSY';
  } else {
    dot.className   = 'avail-dot';
    label.className = 'avail-label';
    label.textContent = 'AVAILABLE';
  }
}

function renderActiveJob(job) {
  document.getElementById('aj-id').textContent      = '#' + job.id;
  document.getElementById('aj-name').textContent    = job.customer_name;
  document.getElementById('aj-phone').textContent   = job.phone;
  document.getElementById('aj-service').textContent = job.service_type;
  document.getElementById('aj-desc').textContent    = job.description;
  document.getElementById('aj-time').textContent    = job.created_at;
}

/* ── FETCH AVAILABLE JOBS ─────────────────────────────────── */
async function fetchJobs() {
  try {
    const url  = `${API}/requests?service_type=${encodeURIComponent(provider.service_type)}`;
    const res  = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    document.getElementById('stat-pending').textContent = data.requests.length;
    document.getElementById('jobs-count').textContent =
      `${data.requests.length} job${data.requests.length !== 1 ? 's' : ''}`;
    renderJobs(data.requests);
  } catch (e) { console.error('Jobs error:', e); }
}

function renderJobs(jobs) {
  const grid = document.getElementById('jobs-grid');
  if (!jobs.length) {
    grid.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">✅</div>
        <div class="empty-title">No pending requests right now</div>
        <div>All ${provider.service_type} requests have been handled. Check back soon.</div>
      </div>`;
    return;
  }
  grid.innerHTML = jobs.map(j => `
    <div class="job-card" id="jcard-${j.id}">
      <div class="job-header">
        <span class="job-id-lbl">Request #${j.id}</span>
        <span class="job-service-chip">${j.service_type}</span>
      </div>
      <div class="job-name">${j.customer_name}</div>
      <div class="job-phone">📞 ${j.phone}</div>
      <div class="job-desc">${j.description}</div>
      <div class="job-footer">
        <span class="job-time">🕒 ${formatTime(j.created_at)}</span>
        <button class="btn btn-blue" onclick="acceptJob(${j.id}, this)">Accept Job →</button>
      </div>
    </div>`).join('');
}

function formatTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) +
    ' · ' + d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

/* ── ACCEPT JOB ───────────────────────────────────────────── */
async function acceptJob(jobId, btn) {
  if (provider.availability === 'BUSY') {
    return showToast('You already have an active job. Complete it first!', 'error');
  }

  btn.disabled    = true;
  btn.textContent = 'Accepting…';

  try {
    const res = await fetch(`${API}/request/${jobId}/accept`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ provider_id: provider.id })
    });
    const data = await res.json();

    if (data.success) {
      showToast('✅ Job accepted! Customer has been notified.');
      await refreshAll();
    } else {
      showToast(data.message, 'error');
      btn.disabled    = false;
      btn.textContent = 'Accept Job →';
    }
  } catch {
    showToast('Server error. Please try again.', 'error');
    btn.disabled    = false;
    btn.textContent = 'Accept Job →';
  }
}

/* ── COMPLETE JOB ─────────────────────────────────────────── */
async function completeJob() {
  if (!activeJobId) return;
  const btn = document.getElementById('btn-complete');
  btn.disabled    = true;
  btn.textContent = 'Completing…';

  try {
    const res = await fetch(`${API}/request/${activeJobId}/complete`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ provider_id: provider.id })
    });
    const data = await res.json();

    if (data.success) {
      showToast('🎉 Job completed! You are now available for new requests.');
      await refreshAll();
    } else {
      showToast(data.message, 'error');
    }
  } catch {
    showToast('Server error. Please try again.', 'error');
  } finally {
    btn.disabled    = false;
    btn.textContent = '✅ Mark as Completed';
  }
}

/* ── INIT ─────────────────────────────────────────────────── */
// initDashboard() is called by provider.html inline script after auth check
