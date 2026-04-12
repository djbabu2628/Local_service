/* ============================================================
   emergency.js — User Dashboard: Provider Browsing, Booking,
   Payment, History & Tracking
   ============================================================ */

const API = 'https://local-service-rvpo.onrender.com/api';

/* ── Toast ────────────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span class="toast-icon">${icons[type] || '✓'}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0'; el.style.transform = 'translateX(40px)';
    el.style.transition = 'all .3s ease';
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

/* ── AUTH GUARD ───────────────────────────────────────────── */
let currentUser = null;
let userLocation = { latitude: null, longitude: null };
let selectedProvider = null;
let selectedPaymentMethod = 'CASH';

function initPage() {
  const raw = localStorage.getItem('lses_user');
  if (!raw) { location.href = 'index.html'; return; }
  currentUser = JSON.parse(raw);

  document.getElementById('user-name-display').textContent = currentUser.name;
  const av = document.getElementById('user-avatar');
  if (av) {
    if (currentUser.profile_photo) {
      av.innerHTML = `<img src="${API.replace('/api','')}${currentUser.profile_photo}" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`;
    } else {
      av.textContent = currentUser.name[0].toUpperCase();
    }
  }

  // Pre-fill booking form
  const nameField = document.getElementById('book-name');
  if (nameField) nameField.value = currentUser.name;
  const phoneField = document.getElementById('book-phone');
  if (phoneField && currentUser.phone) phoneField.value = currentUser.phone;
  const addressField = document.getElementById('book-address');
  if (addressField && currentUser.address) addressField.value = currentUser.address;

  // Set today as default date
  const dateField = document.getElementById('book-date');
  if (dateField) dateField.value = new Date().toISOString().split('T')[0];

  // Use user's saved location
  if (currentUser.latitude && currentUser.longitude) {
    userLocation.latitude = currentUser.latitude;
    userLocation.longitude = currentUser.longitude;
  }

  loadProviders();
  loadHistory();
}

function logout() {
  localStorage.removeItem('lses_user');
  location.href = 'index.html';
}

/* ── DASHBOARD TAB SWITCHING ─────────────────────────────── */
function switchDashTab(tab) {
  document.querySelectorAll('.dash-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.dash-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`dtab-${tab}`).classList.add('active');
  document.getElementById(`dpanel-${tab}`).classList.add('active');

  if (tab === 'history') loadHistory();
}

/* ── LOCATION DETECTION ──────────────────────────────────── */
function detectUserLocation() {
  if (!navigator.geolocation) {
    showToast('Geolocation not available.', 'error');
    return;
  }
  const info = document.getElementById('location-info');
  info.textContent = 'Detecting location…';
  navigator.geolocation.getCurrentPosition(
    pos => {
      userLocation.latitude = pos.coords.latitude;
      userLocation.longitude = pos.coords.longitude;
      info.textContent = `📍 Location: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
      showToast('Location detected! Sorting by nearest.');
      loadProviders();
    },
    () => {
      info.textContent = 'Location access denied.';
      showToast('Location denied. Showing all providers.', 'info');
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

function detectBookingLocation() {
  const status = document.getElementById('book-location-status');
  if (!navigator.geolocation) { status.textContent = 'Not available.'; return; }
  status.textContent = 'Detecting…';
  navigator.geolocation.getCurrentPosition(
    pos => {
      userLocation.latitude = pos.coords.latitude;
      userLocation.longitude = pos.coords.longitude;
      status.textContent = `📍 ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
      showToast('Booking location set.');
    },
    () => { status.textContent = 'Denied. Will use address.'; },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

/* ── PAYMENT METHOD SELECTOR ─────────────────────────────── */
function selectPaymentMethod(chip) {
  document.querySelectorAll('#dpanel-booking .chip-grid .service-chip').forEach(c => c.classList.remove('selected'));
  chip.classList.add('selected');
  selectedPaymentMethod = chip.dataset.value;
}

/* ── PROVIDER LISTING ────────────────────────────────────── */
async function loadProviders() {
  const list = document.getElementById('provider-list');
  list.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><div class="empty-title">Loading providers…</div></div>';

  const serviceType = document.getElementById('filter-service').value;
  const sort = document.getElementById('filter-sort').value;
  const maxPrice = document.getElementById('filter-max-price').value;

  let url = `${API}/providers?sort=${sort}`;
  if (serviceType) url += `&service_type=${encodeURIComponent(serviceType)}`;
  if (userLocation.latitude) url += `&user_lat=${userLocation.latitude}&user_lng=${userLocation.longitude}`;
  if (maxPrice) url += `&max_price=${maxPrice}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) { list.innerHTML = `<div class="empty-state-inline">${data.message}</div>`; return; }

    const providers = data.providers || [];
    if (!providers.length) {
      list.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-title">No providers found</div><div style="color:var(--text-3)">Try adjusting your filters or location.</div></div>';
      return;
    }

    list.innerHTML = providers.map(p => {
      const distText = p.distance_km !== null ? `${p.distance_km.toFixed(1)} km away` : 'Distance unknown';
      const photoHTML = p.profile_photo
        ? `<img src="${API.replace('/api','')}${p.profile_photo}" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`
        : p.name[0].toUpperCase();
      const isSelected = selectedProvider && selectedProvider.id === p.id;
      return `
        <div class="provider-result-card ${isSelected ? 'selected' : ''}" id="prov-card-${p.id}">
          <div class="provider-result-head">
            <div style="display:flex;gap:12px;align-items:center">
              <div style="width:48px;height:48px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px;flex-shrink:0;overflow:hidden">${photoHTML}</div>
              <div>
                <div class="provider-name-row">${p.name}</div>
                <div class="provider-meta-row">${p.service_type} · ${p.experience || 'New'} · ${p.charge_type === 'hourly' ? 'Hourly' : 'Per Visit'}</div>
              </div>
            </div>
            <div class="rating-pill">⭐ ${p.rating}</div>
          </div>
          <div class="provider-detail-line" style="margin-top:8px">📞 ${p.phone} · ${distText}</div>
          <div class="provider-detail-line">📍 ${p.address || 'Address not set'}</div>
          <div class="provider-detail-line" style="margin-top:4px">
            <strong>₹${p.base_charge}</strong> service + ₹${p.platform_fee} platform = <strong style="color:var(--accent)">₹${p.total_charge}</strong>
          </div>
          <div class="provider-card-actions">
            <span class="mini-badge">${p.availability === 'BUSY' ? '🔴 Busy' : '🟢 Available'}</span>
            <button class="btn btn-accent btn-sm" onclick='selectProvider(${JSON.stringify(p).replace(/'/g, "\\'")})'>${isSelected ? '✓ Selected' : 'Select & Book'}</button>
          </div>
        </div>`;
    }).join('');
  } catch {
    list.innerHTML = '<div class="empty-state-inline">Cannot connect to server. Is Flask running?</div>';
  }
}

/* ── SELECT PROVIDER ─────────────────────────────────────── */
function selectProvider(provider) {
  selectedProvider = provider;

  // Update visual selection
  document.querySelectorAll('.provider-result-card').forEach(c => c.classList.remove('selected'));
  const card = document.getElementById(`prov-card-${provider.id}`);
  if (card) card.classList.add('selected');

  // Update booking tab
  document.getElementById('selected-provider-card').style.display = 'block';
  document.getElementById('no-provider-msg').style.display = 'none';
  document.getElementById('btn-book').disabled = false;

  const avatar = document.getElementById('sel-prov-avatar');
  if (provider.profile_photo) {
    avatar.innerHTML = `<img src="${API.replace('/api','')}${provider.profile_photo}" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`;
  } else {
    avatar.textContent = provider.name[0].toUpperCase();
  }
  document.getElementById('sel-prov-name').textContent = provider.name;
  document.getElementById('sel-prov-meta').textContent = `${provider.service_type} · ⭐ ${provider.rating} · ${provider.experience || 'New'}`;

  // Update payment summary
  document.getElementById('pay-service').textContent = `₹${provider.base_charge}`;
  document.getElementById('pay-platform').textContent = `₹${provider.platform_fee}`;
  document.getElementById('pay-total').textContent = `₹${provider.total_charge}`;
  document.getElementById('pay-note').textContent = `✅ Provider: ${provider.name}. Total charges include service fee and platform fee.`;

  showToast(`Selected ${provider.name}. Go to "Book Service" tab to complete.`);
  switchDashTab('booking');
}

function clearSelectedProvider() {
  selectedProvider = null;
  document.getElementById('selected-provider-card').style.display = 'none';
  document.getElementById('no-provider-msg').style.display = 'flex';
  document.getElementById('btn-book').disabled = true;
  document.getElementById('pay-service').textContent = '₹0';
  document.getElementById('pay-platform').textContent = '₹49';
  document.getElementById('pay-total').textContent = '₹0';
  document.getElementById('pay-note').textContent = '💡 Select a provider to see the payment breakdown.';
  document.querySelectorAll('.provider-result-card').forEach(c => c.classList.remove('selected'));
}

/* ── SUBMIT BOOKING ──────────────────────────────────────── */
async function submitBooking() {
  if (!selectedProvider) return showToast('Please select a provider first.', 'error');

  const name = document.getElementById('book-name').value.trim();
  const phone = document.getElementById('book-phone').value.trim();
  const address = document.getElementById('book-address').value.trim();
  const date = document.getElementById('book-date').value;
  const time = document.getElementById('book-time').value;
  const desc = document.getElementById('book-desc').value.trim();

  if (!name || !phone || !address || !date || !time || !desc) {
    return showToast('Please fill all booking fields.', 'error');
  }
  if (!/^\d{10}$/.test(phone)) return showToast('Enter a valid 10-digit phone number.', 'error');

  const btn = document.getElementById('btn-book');
  btn.disabled = true; btn.textContent = 'Booking…';

  try {
    const res = await fetch(`${API}/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.id,
        name, phone,
        service_type: selectedProvider.service_type,
        description: desc,
        provider_id: selectedProvider.id,
        scheduled_date: date,
        scheduled_time: time,
        address,
        user_latitude: userLocation.latitude,
        user_longitude: userLocation.longitude,
        payment_method: selectedPaymentMethod,
      })
    });
    const data = await res.json();

    if (data.success) {
      if (data.payment_method === 'CASH') {
        showToast('🎉 Booking confirmed! Pay cash to the provider on arrival.');
      } else if (data.payment) {
        // Mock payment — auto-verify
        showToast('Processing payment…', 'info');
        await verifyMockPayment(data.booking_id, data.payment);
      } else {
        showToast('Booking created!');
      }

      // Reset form
      document.getElementById('book-desc').value = '';
      clearSelectedProvider();
      loadHistory();
      switchDashTab('history');
    } else {
      showToast(data.message, 'error');
    }
  } catch {
    showToast('Cannot connect to server.', 'error');
  } finally {
    btn.disabled = false; btn.textContent = '🚀 Confirm Booking';
  }
}

async function verifyMockPayment(bookingId, paymentData) {
  try {
    await fetch(`${API}/payment/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        booking_id: bookingId,
        razorpay_order_id: paymentData.order_id,
        razorpay_payment_id: `mock_pay_${bookingId}_${Date.now()}`,
        razorpay_signature: 'mock_signature'
      })
    });
    showToast('🎉 Payment verified! Provider has been notified.');
  } catch {
    showToast('Payment verification issue. Try from booking history.', 'error');
  }
}

/* ── BOOKING HISTORY ─────────────────────────────────────── */
async function loadHistory() {
  const target = document.getElementById('user-history');
  if (!currentUser) return;

  try {
    const res = await fetch(`${API}/bookings/user/${currentUser.id}`);
    const data = await res.json();
    if (!data.success) { target.innerHTML = `<div class="empty-state-inline">${data.message}</div>`; return; }

    const bookings = data.bookings || [];
    if (!bookings.length) {
      target.innerHTML = '<div class="empty-state-inline">No bookings yet. Browse providers and book a service!</div>';
      return;
    }

    target.innerHTML = bookings.map(b => {
      const statusClass = b.status === 'COMPLETED' ? 'badge-completed' : b.status === 'ACCEPTED' ? 'badge-assigned' : 'badge-pending';
      const statusLabel = b.status === 'COMPLETED' ? '✅ Completed' : b.status === 'ACCEPTED' ? '🔵 In Progress' : '⏳ Pending';
      return `
        <article class="history-card">
          <div class="history-card-head">
            <div>
              <div class="history-card-title">#${b.id} · ${b.service_type}</div>
              <div class="history-card-sub">${b.provider_name || 'Provider pending'} · ${formatSlot(b.scheduled_date, b.scheduled_time)}</div>
            </div>
            <div class="history-status-stack">
              <span class="badge ${statusClass}"><span class="badge-dot"></span>${statusLabel}</span>
              <span class="mini-badge">${b.payment_status_label || b.payment_status} · ${b.payment_method || 'ONLINE'}</span>
            </div>
          </div>
          <div class="provider-detail-line">📍 ${b.address || 'No address'}</div>
          <div class="provider-detail-line">💰 ₹${b.total_amount} · ${b.description || ''}</div>
          ${b.completed_at ? `<div class="provider-detail-line" style="color:var(--success)">✅ Completed: ${b.completed_at}</div>` : ''}
        </article>`;
    }).join('');
  } catch {
    target.innerHTML = '<div class="empty-state-inline">Could not load booking history.</div>';
  }
}

function formatSlot(date, time) {
  if (!date && !time) return '—';
  const parsed = new Date(`${date || ''}T${time || '00:00'}`);
  if (isNaN(parsed.getTime())) return `${date || ''} ${time || ''}`.trim();
  return `${parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} · ${parsed.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}`;
}

/* ── TRACK REQUEST ────────────────────────────────────────── */
async function trackRequest() {
  const phone = document.getElementById('track-phone').value.trim();
  if (!phone) return showToast('Enter your phone number to track', 'error');

  const btn = document.getElementById('btn-track');
  btn.disabled = true; btn.textContent = 'Searching…';

  try {
    const res = await fetch(`${API}/track?phone=${encodeURIComponent(phone)}`);
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
    btn.disabled = false; btn.textContent = '🔍 Track Status';
  }
}

function renderTrackResult(req) {
  document.getElementById('tr-id').textContent = '#' + req.id;
  document.getElementById('tr-service').textContent = req.service_type;
  document.getElementById('tr-time').textContent = req.created_at;
  document.getElementById('tr-desc').textContent = req.description;
  document.getElementById('tr-payment').textContent = `${req.payment_status_label || req.payment_status} · ${req.payment_method || 'ONLINE'} · ₹${req.total_amount}`;

  const badge = document.getElementById('tr-badge');
  const statusMap = {
    PENDING: ['badge-pending', '⏳ Waiting for Provider'],
    ACCEPTED: ['badge-assigned', '🔵 Provider Assigned'],
    COMPLETED: ['badge-completed', '✅ Service Completed']
  };
  const [cls, label] = statusMap[req.status] || ['badge-pending', req.status];
  badge.className = `badge ${cls}`;
  badge.innerHTML = `<span class="badge-dot"></span>${label}`;

  const pRow = document.getElementById('tr-provider-row');
  if (req.provider_name) {
    pRow.style.display = 'flex';
    document.getElementById('tr-provider').textContent = `${req.provider_name} · ${req.provider_phone || ''}`;
  } else { pRow.style.display = 'none'; }

  const cRow = document.getElementById('tr-completed-row');
  if (req.completed_at) {
    cRow.style.display = 'flex';
    document.getElementById('tr-completed').textContent = req.completed_at;
  } else { cRow.style.display = 'none'; }

  const order = ['PENDING', 'ACCEPTED', 'COMPLETED'];
  const cur = order.indexOf(req.status);
  const steps = [
    { label: 'Request Submitted', sub: req.created_at },
    { label: req.provider_name ? `Assigned — ${req.provider_name}` : 'Waiting for a Provider', sub: req.status === 'ACCEPTED' ? 'Provider is on the way!' : '—' },
    { label: 'Service Completed', sub: req.completed_at || 'Pending…' }
  ];
  const tl = document.getElementById('tr-timeline');
  tl.innerHTML = steps.map((s, i) => {
    let dotCls = '';
    if (i < cur) dotCls = 'done';
    else if (i === cur) dotCls = 'active';
    return `<div class="tl-step">
      <div class="tl-dot ${dotCls}"></div>
      <div class="tl-content"><div class="tl-lbl">${s.label}</div><div class="tl-sub">${s.sub}</div></div>
    </div>`;
  }).join('');
}

/* ── INIT ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initPage();
  const trackInput = document.getElementById('track-phone');
  if (trackInput) {
    trackInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') trackRequest();
    });
  }
});
