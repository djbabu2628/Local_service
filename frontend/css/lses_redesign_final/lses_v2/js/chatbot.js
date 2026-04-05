/* ============================================================
   chatbot.js  —  AI Chatbot UI + rule-based responses
   Floating chatbot available on all pages
   ============================================================ */

const BOT_NAME = 'ServiceBot';

const RESPONSES = [
  {
    patterns: ['plumb', 'pipe', 'water', 'leak', 'tap', 'drain', 'flush'],
    reply: '🔧 For plumbing issues like leaks, pipe bursts or blocked drains — go to the Emergency page and select "Plumber" as your service type. We\'ll connect you with a verified plumber near you!'
  },
  {
    patterns: ['electric', 'wiring', 'power', 'switch', 'light', 'circuit', 'shock'],
    reply: '⚡ Electrical emergencies are serious! Submit an emergency request on the Emergency page and choose "Electrician". Our licensed electricians respond quickly. If it\'s life-threatening, call 101 first!'
  },
  {
    patterns: ['mechanic', 'car', 'vehicle', 'engine', 'tyre', 'flat', 'breakdown'],
    reply: '🔩 For vehicle breakdowns, tyre punctures or engine issues — select "Mechanic" in the emergency form. Share your location in the description for faster service!'
  },
  {
    patterns: ['ac', 'air condition', 'cooling', 'heater', 'hvac', 'fan'],
    reply: '❄️ AC and HVAC repairs? Select "AC Repair" in the emergency request form. Our technicians are equipped to handle all major brands!'
  },
  {
    patterns: ['carpenter', 'door', 'furniture', 'wood', 'cabinet', 'lock'],
    reply: '🚪 For carpentry, door repairs or furniture fixes, select "Carpenter" in the form. Provide a brief description and we\'ll match you with the right expert!'
  },
  {
    patterns: ['track', 'status', 'where', 'update', 'assigned', 'pending', 'complete'],
    reply: '📍 To track your request: scroll down on the Emergency page, enter your registered phone number in the "Track Your Request" section and click Track. You\'ll see real-time status!'
  },
  {
    patterns: ['register', 'signup', 'create account', 'new user'],
    reply: '👤 To register, click "Create Account" tab on the home page. Enter your name, email and a password. After registration, log in to raise emergency requests!'
  },
  {
    patterns: ['provider', 'technician', 'join', 'work', 'service provider'],
    reply: '🛠️ Want to become a service provider? Click "Provider Login" in the top nav, then choose "Register as Provider". Enter your details and select your service specialisation!'
  },
  {
    patterns: ['emergency', 'urgent', 'help', 'sos', 'fast', 'quickly'],
    reply: '🚨 For emergencies: log in → go to Emergency page → fill the form with your name, phone, service type and problem description → Submit! Available providers in your area will be notified immediately.'
  },
  {
    patterns: ['price', 'cost', 'charge', 'fee', 'rate', 'payment'],
    reply: '💰 Service charges are agreed directly between you and the provider. LSES is a free platform to connect you with technicians. Always confirm charges before work begins!'
  },
  {
    patterns: ['hello', 'hi', 'hey', 'namaste', 'hii', 'helo'],
    reply: '👋 Hello! I\'m ServiceBot, your LSES assistant. I can help you with:\n• Submitting emergency requests\n• Tracking your request status\n• Information about our services\n\nWhat do you need help with?'
  },
  {
    patterns: ['thank', 'thanks', 'dhanyawad', 'shukriya'],
    reply: '😊 You\'re welcome! Stay safe and feel free to ask anything else. We\'re here 24/7!'
  }
];

const DEFAULT_REPLY = '🤔 I\'m not sure about that specific question. You can:\n• Submit a request on the Emergency page\n• Track your request status by phone number\n• Visit our Help section\n\nOr type your question more specifically — e.g. "how to track request" or "I need a plumber".';

/* ── GET BOT RESPONSE ─────────────────────────────────────── */
function getBotResponse(userMsg) {
  const lower = userMsg.toLowerCase();
  for (const item of RESPONSES) {
    if (item.patterns.some(p => lower.includes(p))) {
      return item.reply;
    }
  }
  return DEFAULT_REPLY;
}

/* ── APPEND MESSAGE ───────────────────────────────────────── */
function appendMsg(text, sender) {
  const msgs = document.getElementById('chat-messages');
  const div  = document.createElement('div');
  div.className = `msg ${sender}`;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

/* ── TYPING INDICATOR ─────────────────────────────────────── */
function showTyping() {
  const msgs = document.getElementById('chat-messages');
  const div  = document.createElement('div');
  div.className = 'msg bot';
  div.id = 'typing-indicator';
  div.textContent = '…';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}
function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

/* ── SEND MESSAGE ─────────────────────────────────────────── */
function sendMessage() {
  const input = document.getElementById('chat-input');
  const text  = input.value.trim();
  if (!text) return;

  appendMsg(text, 'user');
  input.value = '';

  showTyping();
  setTimeout(() => {
    removeTyping();
    const reply = getBotResponse(text);
    appendMsg(reply, 'bot');
  }, 700 + Math.random() * 400);
}

/* ── TOGGLE CHAT WINDOW ───────────────────────────────────── */
function toggleChat() {
  const win = document.getElementById('chat-window');
  const fab = document.getElementById('chat-fab');
  const isOpen = win.classList.contains('open');
  if (isOpen) {
    win.classList.remove('open');
    fab.textContent = '💬';
  } else {
    win.classList.add('open');
    fab.textContent = '✕';
    // Show welcome message on first open
    const msgs = document.getElementById('chat-messages');
    if (msgs && msgs.children.length === 0) {
      setTimeout(() => appendMsg('👋 Hi! I\'m ServiceBot. How can I help you today? Type "help" to see what I can do!', 'bot'), 300);
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
