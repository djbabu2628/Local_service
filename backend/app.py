"""
app.py — LSES Flask Main Server
Runs on http://localhost:5000 (local development only)
"""

from flask import Flask
from flask_cors import CORS

from database.db import init_db
from routes.auth      import auth_bp
from routes.requests  import requests_bp
from routes.providers import providers_bp
from chatbot.chatbot  import chatbot_bp

# ── Create App ───────────────────────────────────────────────
app = Flask(__name__)

# ── CORS — allow all origins for local development ──────────
CORS(app,
     origins="*",
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# NOTE: No @app.after_request needed — flask-cors handles all
# CORS headers automatically. Adding manual headers causes
# duplicate Access-Control-Allow-Origin which breaks browsers.

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
    print("🚀 Starting Flask server on http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)