"""
chatbot/chatbot.py — LSES AI Chatbot
POST /api/chat — Returns a smart reply based on user message.
Uses rule-based NLP. Can be upgraded to OpenAI/Gemini API later.
"""

from flask import Blueprint, request, jsonify
from services.service_classifier import classify_service, get_all_services
import re

chatbot_bp = Blueprint('chatbot', __name__)

# ── Knowledge Base ────────────────────────────────────────────
RESPONSES = {
    # Greetings
    'greet': {
        'patterns': ['hello', 'hi', 'hey', 'good morning', 'good afternoon',
                     'good evening', 'namaste', 'hii', 'helo'],
        'reply': "Hello! 👋 Welcome to <b>LSES — Local Service Emergency System</b>. "
                 "I'm here to help you with emergency service requests, tracking, and more. "
                 "How can I assist you today?"
    },
    # How to raise request
    'raise_request': {
        'patterns': ['how to raise', 'how to submit', 'how do i request', 'request service',
                     'how to book', 'raise emergency', 'need help', 'submit request',
                     'how to get help', 'how to apply'],
        'reply': "To raise an emergency request: <br>"
                 "1️⃣ Make sure you're logged in as a <b>User</b><br>"
                 "2️⃣ Fill in your <b>name, phone number</b><br>"
                 "3️⃣ Select the <b>service type</b> (e.g. Plumber, Electrician)<br>"
                 "4️⃣ Describe the problem briefly<br>"
                 "5️⃣ Click <b>Submit Emergency Request</b> 🚨<br><br>"
                 "A provider in your area will be notified immediately!"
    },
    # Track request
    'track': {
        'patterns': ['track', 'status', 'where is', 'check request', 'my request',
                     'request status', 'what happened', 'update', 'how to track'],
        'reply': "You can track your request status easily: <br>"
                 "1️⃣ Go to the <b>Emergency Dashboard</b><br>"
                 "2️⃣ Scroll to the <b>Track Your Request</b> card<br>"
                 "3️⃣ Enter your registered <b>phone number</b><br>"
                 "4️⃣ Click <b>Track Request Status</b> 🔍<br><br>"
                 "You'll see: ⏳ Waiting → 🔵 Assigned → ✅ Completed"
    },
    # Services available
    'services': {
        'patterns': ['services', 'what service', 'which service', 'available service',
                     'types of service', 'kya service', 'service list', 'categories'],
        'reply': "We currently support these <b>emergency services</b>: <br><br>"
                 "🔧 <b>Plumber</b> — Pipe leaks, blockages, taps<br>"
                 "⚡ <b>Electrician</b> — Wiring, power issues, short circuits<br>"
                 "🔩 <b>Mechanic</b> — Car/bike breakdowns, tyre punctures<br>"
                 "❄️ <b>AC Repair</b> — Cooling issues, gas refill<br>"
                 "🚪 <b>Carpenter</b> — Door/window/furniture repairs<br>"
                 "🏠 <b>Handyman</b> — General repairs and installations<br><br>"
                 "More services are being added regularly!"
    },
    # Response time
    'response_time': {
        'patterns': ['how long', 'time', 'wait', 'minutes', 'hours', 'when',
                     'how fast', 'quickly', 'urgent', 'immediate', 'asap'],
        'reply': "Our average response time is <b>under 5 minutes</b>! ⚡<br><br>"
                 "After you submit a request:<br>"
                 "• Nearby available providers are <b>notified instantly</b><br>"
                 "• Provider dashboards <b>auto-refresh every 10 seconds</b><br>"
                 "• Once a provider accepts, you'll see their name in tracking<br><br>"
                 "Emergency requests are given <b>top priority</b>! 🚨"
    },
    # Provider info
    'provider': {
        'patterns': ['provider', 'technician', 'worker', 'professional', 'expert',
                     'who comes', 'who will', 'service provider', 'join as provider',
                     'register as provider', 'become provider'],
        'reply': "All LSES service providers are <b>verified local professionals</b>. ✅<br><br>"
                 "<b>To register as a Provider:</b><br>"
                 "1️⃣ Click <b>Provider Portal</b> in the top navigation<br>"
                 "2️⃣ Click <b>Register</b> tab<br>"
                 "3️⃣ Fill in your name, phone, email, service type & password<br>"
                 "4️⃣ Start accepting emergency jobs immediately! 💼"
    },
    # Cost / charges
    'cost': {
        'patterns': ['cost', 'price', 'charge', 'fee', 'money', 'payment', 'free',
                     'how much', 'rate', 'rupee', 'rs', 'paisa', 'billing', 'pay'],
        'reply': "💰 <b>LSES is completely free</b> to use for submitting requests!<br><br>"
                 "Service charges are agreed directly between you and the provider "
                 "when they arrive. Pricing depends on:<br>"
                 "• Type of service needed<br>"
                 "• Complexity of the work<br>"
                 "• Time and materials required<br><br>"
                 "We recommend discussing the estimate before work begins. 🤝"
    },
    # Login / Account
    'account': {
        'patterns': ['login', 'sign in', 'register', 'account', 'password', 'forgot',
                     'sign up', 'create account', 'log in', 'logout', 'session'],
        'reply': "🔐 <b>Account Help:</b><br><br>"
                 "• <b>New user?</b> Click 'Create Account' on the home page<br>"
                 "• <b>Existing user?</b> Use 'Sign In' with your email & password<br>"
                 "• <b>Provider?</b> Go to Provider Portal → Sign In<br><br>"
                 "⚠️ If you forgot your password, please re-register with the same email "
                 "(password reset feature coming soon)."
    },
    # Emergency types
    'emergency': {
        'patterns': ['emergency', 'urgent', 'critical', 'serious', 'pipe burst',
                     'no power', 'flood', 'fire', 'danger', 'gas leak'],
        'reply': "🚨 <b>Emergency detected!</b><br><br>"
                 "For <b>life-threatening emergencies</b> (fire, gas explosion, medical), "
                 "please call <b>112</b> (India Emergency) immediately!<br><br>"
                 "For urgent home services like burst pipes, power outages, or floods:<br>"
                 "➡️ Submit a request on LSES right now — our providers respond in minutes! ⚡"
    },
    # Goodbye
    'bye': {
        'patterns': ['bye', 'goodbye', 'see you', 'thanks', 'thank you', 'ok done',
                     'that is all', 'no more', 'exit', 'quit'],
        'reply': "You're welcome! 😊 Stay safe and don't hesitate to reach out if you need "
                 "emergency services. <b>LSES is available 24/7</b> for you! 🚨"
    },
}

# ── Fallback responses (rotated for variety) ──────────────────
FALLBACKS = [
    "I'm not sure I understood that. Could you try asking about:<br>"
    "• How to <b>submit a request</b><br>"
    "• How to <b>track</b> your request<br>"
    "• <b>Services</b> we offer<br>"
    "• <b>Response time</b> or charges",

    "Hmm, I didn't quite get that! 🤔 I can help you with:<br>"
    "• Submitting emergency requests<br>"
    "• Tracking your request status<br>"
    "• Information about our services<br>"
    "• Becoming a service provider",
]

_fallback_idx = 0


def get_reply(message: str) -> str:
    global _fallback_idx
    text = message.lower().strip()

    # Check each intent
    for intent, data in RESPONSES.items():
        for pattern in data['patterns']:
            if pattern in text:
                return data['reply']

    # Try service classifier for problem descriptions
    detected = classify_service(text)
    if detected:
        return (f"It sounds like you might need a <b>{detected}</b>! 🔧<br><br>"
                f"Here's what to do:<br>"
                f"1️⃣ Go to the <b>Emergency Dashboard</b><br>"
                f"2️⃣ Select <b>{detected}</b> as your service type<br>"
                f"3️⃣ Describe your problem and submit the request<br><br>"
                f"Nearby {detected.lower()}s will be notified immediately! 🚨")

    # Fallback
    reply = FALLBACKS[_fallback_idx % len(FALLBACKS)]
    _fallback_idx += 1
    return reply


# ── Route ─────────────────────────────────────────────────────
@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    data    = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify(success=False, reply="Please type a message."), 400

    reply = get_reply(message)
    return jsonify(success=True, reply=reply)
