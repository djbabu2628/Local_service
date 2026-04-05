/* ============================================================
   emergency.js  —  Emergency request form + tracking logic
   Used by: emergency.html
   ============================================================ */
// ✅ LOCAL DEVELOPMENT — Flask backend running on localhost
const API = 'http://localhost:5000/api';

function showToast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span class="toast-icon">${icons[type]||'✓'}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => { el.style.animation = 'slideIn .3s ease reverse'; setTimeout(() => el.remove(), 280); }, 3500);
}

/* ── AUTH GUARD ───────────────────────────────────────────── */
let currentUser = null;

function initPage() {
  const raw = localStorage.getItem('lses_user');
  if (!raw) { location.href = 'index.html'; return; }
  currentUser = JSON.parse(raw);

  document.getElementById('user-name-display').textContent = currentUser.name;
  const av = document.getElementById('user-avatar');
  if (av) av.textContent = currentUser.name[0].toUpperCase();

  // Pre-fill name in form
  const nameField = document.getElementById('req-name');
  if (nameField) nameField.value = currentUser.name;
}

function logout() {
  localStorage.removeItem('lses_user');
  location.href = 'index.html';
}

/* ── SUBMIT EMERGENCY REQUEST ─────────────────────────────── */
async function submitRequest() {
  const name    = document.getElementById('req-name').value.trim();
  const phone   = document.getElementById('req-phone').value.trim();
  const service = document.getElementById('req-service').value;
  const desc    = document.getElementById('req-desc').value.trim();

  if (!name || !phone || !service || !desc) {
    return showToast('Please fill all fields', 'error');
  }
  if (!/^\d{10}$/.test(phone)) {
    return showToast('Enter a valid 10-digit phone number', 'error');
  }

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.textContent = 'Submitting…';

  try {
    const res = await fetch(`${API}/request`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        user_id: currentUser.id, name, phone,
        service_type: service, description: desc
      })
    });
    const data = await res.json();

    if (data.success) {
      showToast('🚨 Emergency request submitted! Providers are being notified.');
      // Clear form (keep name)
      document.getElementById('req-phone').value   = '';
      document.getElementById('req-service').value = '';
      document.getElementById('req-desc').value    = '';
      // Auto-fill track field and show status
      document.getElementById('track-phone').value = phone;
      setTimeout(() => trackRequest(), 1200);
    } else {
      showToast(data.message, 'error');
    }
  } catch {
    showToast('Cannot connect to server. Is Flask running?', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🚨 Submit Emergency Request';
  }
}

/* ── TRACK REQUEST ────────────────────────────────────────── */
async function trackRequest() {
  const phone = document.getElementById('track-phone').value.trim();
  if (!phone) return showToast('Enter your phone number to track', 'error');

  const btn = document.getElementById('btn-track');
  btn.disabled = true;
  btn.textContent = 'Searching…';

  try {
    const res  = await fetch(`${API}/track?phone=${encodeURIComponent(phone)}`);
    const data = await res.json();

    if (!data.success) {
      showToast(data.message, 'error');
      document.getElementById('track-result').style.display = 'none';
      return;
    }
    renderTrackResult(data.request);
    document.getElementById('track-result').style.display = 'block';
    showToast('Request found!', 'info');
  } catch {
    showToast('Cannot connect to server.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 Track Status';
  }
}

/* ── RENDER TRACK RESULT ──────────────────────────────────── */
function renderTrackResult(req) {
  document.getElementById('tr-id').textContent      = '#' + req.id;
  document.getElementById('tr-service').textContent = req.service_type;
  document.getElementById('tr-time').textContent    = req.created_at;
  document.getElementById('tr-desc').textContent    = req.description;

  // Status badge
  const badge = document.getElementById('tr-badge');
  const statusMap = {
    PENDING:   ['badge-pending',   '⏳ Waiting for Provider'],
    ASSIGNED:  ['badge-assigned',  '🔵 Provider Assigned'],
    COMPLETED: ['badge-completed', '✅ Service Completed']
  };
  const [cls, label] = statusMap[req.status] || ['badge-pending', req.status];
  badge.className = `badge ${cls}`;
  badge.innerHTML = `<span class="badge-dot"></span>${label}`;

  // Provider info
  const pRow = document.getElementById('tr-provider-row');
  if (req.provider_name) {
    pRow.style.display = 'flex';
    document.getElementById('tr-provider').textContent = req.provider_name;
  } else {
    pRow.style.display = 'none';
  }

  // Completion time
  const cRow = document.getElementById('tr-completed-row');
  if (req.completed_at) {
    cRow.style.display = 'flex';
    document.getElementById('tr-completed').textContent = req.completed_at;
  } else {
    cRow.style.display = 'none';
  }

  // Timeline
  const order = ['PENDING', 'ASSIGNED', 'COMPLETED'];
  const cur   = order.indexOf(req.status);
  const steps = [
    { label: 'Request Submitted',  sub: req.created_at },
    { label: req.provider_name ? `Assigned — ${req.provider_name}` : 'Waiting for a Provider', sub: req.status === 'ASSIGNED' ? 'Provider is on the way!' : '—' },
    { label: 'Service Completed',  sub: req.completed_at || 'Pending…' }
  ];
  const tl = document.getElementById('tr-timeline');
  tl.innerHTML = steps.map((s, i) => {
    let dotCls = '';
    if (i < cur)       dotCls = 'done';
    else if (i === cur) dotCls = 'active';
    return `<div class="tl-step">
      <div class="tl-dot ${dotCls}"></div>
      <div><div class="tl-lbl">${s.label}</div><div class="tl-sub">${s.sub}</div></div>
    </div>`;
  }).join('');
}

/* ── ENTER KEY SUPPORT ────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initPage();
  const trackInput = document.getElementById('track-phone');
  if (trackInput) {
    trackInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') trackRequest();
    });
  }
});
