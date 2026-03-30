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

# ── CORS Fix — sab origins allow karo ───────────────────────
CORS(app,
     origins="*",
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Preflight OPTIONS request handle karo
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

# ── Register Blueprints ──────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(requests_bp)
app.register_blueprint(providers_bp)
app.register_blueprint(chatbot_bp)

# ── Health Check ─────────────────────────────────────────────
@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'LSES API is running'}

# ── Database init ────────────────────────────────────────────
print("🚨 Initializing LSES database…")
init_db()
print("✅ Database ready.")

# ── Entry Point ──────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)