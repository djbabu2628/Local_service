/* ============================================================
   chatbot.js — Calls backend /api/chat, renders HTML replies
   iOS 26 Liquid Glass Edition
   ============================================================ */

const CHATBOT_API = 'https://local-service-rvpo.onrender.com/api';

/* ── APPEND MESSAGE ───────────────────────────────────────── */
function appendMsg(text, sender) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg ${sender}`;

  if (sender === 'bot') {
    div.innerHTML = text;
  } else {
    div.textContent = text;
  }

  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

/* ── TYPING INDICATOR ─────────────────────────────────────── */
function showTyping() {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-typing';
  div.id = 'typing-indicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

/* ── SEND MESSAGE — calls backend /api/chat ───────────────── */
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  appendMsg(text, 'user');
  input.value = '';
  showTyping();

  try {
    const res = await fetch(`${CHATBOT_API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    removeTyping();

    if (data.reply) {
      appendMsg(data.reply, 'bot');
    } else {
      appendMsg('Sorry, I could not understand that. Please try again.', 'bot');
    }
  } catch {
    removeTyping();
    appendMsg('⚠️ Cannot connect to server. Is Flask running on localhost:5000?', 'bot');
  }
}

/* ── TOGGLE CHAT WINDOW ───────────────────────────────────── */
function toggleChat() {
  const win = document.getElementById('chat-window');
  const fab = document.getElementById('chat-fab');
  const isOpen = win.classList.contains('open');

  if (isOpen) {
    win.classList.remove('open');
    fab.classList.remove('active');
    fab.innerHTML = '<span>💬</span><span class="fab-text">Ask ServiceBot</span>';
  } else {
    win.classList.add('open');
    fab.classList.add('active');
    fab.innerHTML = '✕';

    const msgs = document.getElementById('chat-messages');
    if (msgs && msgs.children.length === 0) {
      setTimeout(() => appendMsg('👋 Hi! I\'m <b>ServiceBot</b>. How can I help you today? Type <b>"help"</b> to see what I can do!', 'bot'), 300);
    }
    setTimeout(() => document.getElementById('chat-input').focus(), 400);
  }
}

/* ── EVENT LISTENERS ──────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input');
  if (input) {
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') sendMessage();
    });
  }
});
