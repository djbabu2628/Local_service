"""
app.py — LSES Flask Main Server
"""

import os
from flask import Flask
from flask_cors import CORS

from database.db import init_db
from routes.auth      import auth_bp
from routes.requests  import requests_bp
from routes.providers import providers_bp
from chatbot.chatbot  import chatbot_bp

# ── Create App ───────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Register Blueprints ──────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(requests_bp)
app.register_blueprint(providers_bp)
app.register_blueprint(chatbot_bp)

# ── Health Check ─────────────────────────────────────────────
@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'LSES API is running'}

# ── Database init — YAHAN HONA CHAHIYE (gunicorn ke liye) ────
# Gunicorn __main__ block nahi chalata — isliye upar rakha
print("🚨 Initializing LSES database…")
init_db()
print("✅ Database ready.")

# ── Entry Point (local development ke liye) ──────────────────
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)