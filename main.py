from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import uuid
import hashlib

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory opslag
users = {}
banned_devices = set()

# Beveiliging: wachtwoorden hashen
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Unieke apparaat-ID opvragen via header (bijv. via app)
def get_device_id():
    return request.headers.get('X-Device-ID')

# Alleen 1 account per device toestaan
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    device_id = get_device_id()

    if device_id in banned_devices:
        return jsonify({"success": False, "error": "Dit apparaat is geblokkeerd."}), 403

    if device_id in [u['device_id'] for u in users.values()]:
        return jsonify({"success": False, "error": "Er is al een account geregistreerd op dit apparaat."}), 403

    if username in users:
        return jsonify({"success": False, "error": "Gebruikersnaam bestaat al."}), 400

    users[username] = {
        'password': hash_password(password),
        'device_id': device_id,
        'is_admin': False
    }
    return jsonify({"success": True}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    device_id = get_device_id()

    if device_id in banned_devices:
        return jsonify({"success": False, "error": "Apparaat is geblokkeerd."}), 403

    user = users.get(username)
    if not user or user['password'] != hash_password(password):
        return jsonify({"success": False, "error": "Ongeldige login"}), 403

    return jsonify({"success": True, "is_admin": user.get("is_admin", False)}), 200

@app.route('/admin/ban', methods=['POST'])
def ban_device():
    data = request.json
    username = data['admin']
    password = data['password']
    device_to_ban = data['device_id']

    admin = users.get(username)
    if not admin or admin['password'] != hash_password(password) or not admin.get("is_admin", False):
        return jsonify({"success": False, "error": "Geen toegang"}), 403

    banned_devices.add(device_to_ban)
    return jsonify({"success": True, "banned": list(banned_devices)})

@app.route('/admin/make_admin', methods=['POST'])
def make_admin():
    data = request.json
    admin_user = data['admin']
    password = data['password']
    target = data['target']

    admin = users.get(admin_user)
    if not admin or admin['password'] != hash_password(password) or not admin.get("is_admin", False):
        return jsonify({"success": False, "error": "Geen toegang"}), 403

    if target not in users:
        return jsonify({"success": False, "error": "Doelgebruiker bestaat niet."}), 404

    users[target]["is_admin"] = True
    return jsonify({"success": True})

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)
