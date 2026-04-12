"""
app.py - LSES Flask main server.
Runs on http://localhost:5000 for local development.
Serves both API and frontend static files.
"""

import os
import uuid
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

from chatbot.chatbot import chatbot_bp
from database.db import init_db, UPLOAD_DIR
from routes.auth import auth_bp
from routes.providers import providers_bp
from routes.requests import requests_bp
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(__name__)

CORS(
    app,
    origins='*',
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
)

app.register_blueprint(auth_bp)
app.register_blueprint(requests_bp)
app.register_blueprint(providers_bp)
app.register_blueprint(chatbot_bp)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── API Routes ────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return {'status': 'ok', 'message': 'LSES API is running'}


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a profile photo. Returns the URL to access the image."""
    if 'file' not in request.files:
        return jsonify(success=False, message='No file provided.'), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message='No file selected.'), 400

    if not allowed_file(file.filename):
        return jsonify(success=False, message='File type not allowed. Use PNG, JPG, GIF, or WebP.'), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    url = f'/uploads/{filename}'
    return jsonify(success=True, message='File uploaded successfully.', url=url, filename=filename), 201


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files."""
    return send_from_directory(UPLOAD_DIR, filename)


# ── Frontend Static Serving ──────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_frontend(filename):
    """Serve any static frontend file (HTML, CSS, JS, images)."""
    filepath = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(filepath):
        return send_from_directory(FRONTEND_DIR, filename)
    # Fallback to index for SPA-like behavior
    return send_from_directory(FRONTEND_DIR, 'index.html')


print('[LSES] Initializing database...')
init_db()
print('[LSES] Database ready.')
print(f'[LSES] Frontend directory: {FRONTEND_DIR}')


if __name__ == '__main__':
    print('[LSES] Starting Flask server on http://localhost:5000')
    app.run(host='127.0.0.1', port=5000, debug=True)
