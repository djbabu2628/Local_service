/* ============================================================
   main.js  —  User-side auth logic (index.html)
   ============================================================ */

// ✅ PRODUCTION URL — Railway backend
// Isko apne Railway deploy hone ke baad milne wale URL se replace karo
// Example: https://lses-backend-production.up.railway.app/api
const API = "https://YOUR-RAILWAY-URL.up.railway.app/api";

function showToast(msg, type="success") {
  const c = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = "toast " + type;
  const icons = {success:"✓", error:"✕", info:"ℹ"};
  el.innerHTML = `<span class="toast-icon">${icons[type]||"✓"}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => { el.style.animation = "slideIn .3s ease reverse"; setTimeout(()=>el.remove(),280); }, 3500);
}

function switchTab(tab) {
  document.querySelectorAll(".tab").forEach((t,i) => {
    t.classList.toggle("active", (tab==="login"&&i===0)||(tab==="register"&&i===1));
  });
  document.getElementById("panel-login").classList.toggle("active", tab==="login");
  document.getElementById("panel-register").classList.toggle("active", tab==="register");
}

async function doRegister() {
  const name     = document.getElementById("reg-name").value.trim();
  const email    = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  if (!name||!email||!password) return showToast("Please fill all fields","error");
  if (password.length<6) return showToast("Password must be at least 6 characters","error");
  const btn = document.getElementById("btn-register");
  btn.disabled=true; btn.textContent="Creating account…";
  try {
    const res = await fetch(API+"/user/register", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email,password})});
    const data = await res.json();
    if (data.success) { showToast("Account created! Please sign in."); setTimeout(()=>switchTab("login"),1000); }
    else showToast(data.message,"error");
  } catch { showToast("Cannot connect to server. Is Flask running?","error"); }
  finally { btn.disabled=false; btn.textContent="Create Account →"; }
}

async function doLogin() {
  const email    = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  if (!email||!password) return showToast("Please fill all fields","error");
  const btn = document.getElementById("btn-login");
  btn.disabled=true; btn.textContent="Signing in…";
  try {
    const res = await fetch(API+"/user/login", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
    const data = await res.json();
    if (data.success) {
      localStorage.setItem("lses_user", JSON.stringify(data.user));
      showToast("Welcome back, "+data.user.name+"! Redirecting…");
      setTimeout(()=>(location.href="emergency.html"),900);
    } else showToast(data.message,"error");
  } catch { showToast("Cannot connect to server. Is Flask running?","error"); }
  finally { btn.disabled=false; btn.textContent="Sign In →"; }
}

document.addEventListener("keydown", e => {
  if (e.key!=="Enter") return;
  const isLogin = document.getElementById("panel-login").classList.contains("active");
  isLogin ? doLogin() : doRegister();
});

window.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("lses_user")) {
    showToast("Already logged in. Redirecting…","info");
    setTimeout(()=>(location.href="emergency.html"),1000);
  }
});
