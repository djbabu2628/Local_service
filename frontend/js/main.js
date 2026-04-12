/* ============================================================
   main.js — User auth logic (index.html)
   iOS 26 Liquid Glass Edition — Enhanced with full profile
   ============================================================ */

const API = "http://localhost:5000/api";

let registerLocation = { latitude: null, longitude: null };

function showToast(msg, type = "success") {
  const c = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = "toast " + type;
  const icons = { success: "✓", error: "✕", info: "ℹ" };
  el.innerHTML = `<span class="toast-icon">${icons[type] || "✓"}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transform = "translateX(40px)";
    el.style.transition = "all .3s ease";
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

function switchTab(tab) {
  document.querySelectorAll(".tab").forEach((t, i) => {
    t.classList.toggle("active", (tab === "login" && i === 0) || (tab === "register" && i === 1));
  });
  document.getElementById("panel-login").classList.toggle("active", tab === "login");
  document.getElementById("panel-register").classList.toggle("active", tab === "register");
}

/* ── Location Detection ────────────────────────────────────── */
function captureUserLocation() {
  const status = document.getElementById("reg-location-status");
  if (!navigator.geolocation) {
    status.textContent = "Geolocation not available in this browser.";
    showToast("Geolocation not available.", "error");
    return;
  }
  status.textContent = "Detecting location…";
  navigator.geolocation.getCurrentPosition(
    pos => {
      registerLocation.latitude = pos.coords.latitude;
      registerLocation.longitude = pos.coords.longitude;
      status.textContent = `📍 ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
      showToast("Location detected successfully!");
    },
    () => {
      status.textContent = "Location denied. Enter address manually.";
      showToast("Location access denied.", "info");
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

/* ── Photo Preview ─────────────────────────────────────────── */
function previewPhoto(input, previewId) {
  const preview = document.getElementById(previewId);
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.innerHTML = `<img src="${e.target.result}" style="width:100%;height:100%;object-fit:cover;border-radius:50%"/>`;
    };
    reader.readAsDataURL(input.files[0]);
  }
}

/* ── Upload Photo ──────────────────────────────────────────── */
async function uploadPhoto(fileInput) {
  if (!fileInput || !fileInput.files || !fileInput.files[0]) return '';
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  try {
    const res = await fetch(API + '/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) return data.url;
    showToast(data.message || 'Photo upload failed.', 'error');
  } catch {
    showToast('Could not upload photo.', 'error');
  }
  return '';
}

/* ── Register ──────────────────────────────────────────────── */
async function doRegister() {
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const phone = document.getElementById("reg-phone").value.trim();
  const address = document.getElementById("reg-address").value.trim();

  if (!name || !email || !password) return showToast("Name, email and password are required.", "error");
  if (password.length < 6) return showToast("Password must be at least 6 characters", "error");

  const btn = document.getElementById("btn-register");
  btn.disabled = true; btn.textContent = "Creating account…";

  try {
    // Upload photo first if selected
    const photoUrl = await uploadPhoto(document.getElementById("reg-photo"));

    const res = await fetch(API + "/user/register", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name, email, password, phone, address,
        latitude: registerLocation.latitude,
        longitude: registerLocation.longitude,
        profile_photo: photoUrl
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast("Account created! Please sign in.");
      setTimeout(() => switchTab("login"), 1000);
    } else showToast(data.message, "error");
  } catch { showToast("Cannot connect to server. Is Flask running?", "error"); }
  finally { btn.disabled = false; btn.textContent = "Create Account →"; }
}

/* ── Login ─────────────────────────────────────────────────── */
async function doLogin() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  if (!email || !password) return showToast("Please fill all fields", "error");
  const btn = document.getElementById("btn-login");
  btn.disabled = true; btn.textContent = "Signing in…";
  try {
    const res = await fetch(API + "/user/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.success) {
      localStorage.setItem("lses_user", JSON.stringify(data.user));
      showToast("Welcome back, " + data.user.name + "! Redirecting…");
      setTimeout(() => (location.href = "emergency.html"), 900);
    } else showToast(data.message, "error");
  } catch { showToast("Cannot connect to server. Is Flask running?", "error"); }
  finally { btn.disabled = false; btn.textContent = "Sign In →"; }
}

document.addEventListener("keydown", e => {
  if (e.key !== "Enter") return;
  const isLogin = document.getElementById("panel-login").classList.contains("active");
  isLogin ? doLogin() : doRegister();
});

window.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("lses_user")) {
    showToast("Already logged in. Redirecting…", "info");
    setTimeout(() => (location.href = "emergency.html"), 1000);
  }
});
