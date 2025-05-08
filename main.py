from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Laat verbinding toe vanaf webpagina's

# Tijdelijke opslag (in geheugen)
users = {}
chat_history = []

@app.route('/')
def home():
    return "✅ Server draait!"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users:
        return jsonify({'status': 'exists', 'message': 'Gebruikersnaam bestaat al.'}), 400

    users[username] = password
    return jsonify({'status': 'success', 'message': 'Account aangemaakt!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if users.get(username) == password:
        return jsonify({'status': 'success', 'message': 'Inloggen geslaagd!'}), 200
    return jsonify({'status': 'failure', 'message': 'Ongeldige inloggegevens'}), 401

@app.route('/send', methods=['POST'])
def send():
    data = request.get_json()
    username = data.get('username')
    message = data.get('message')

    if not username or not message:
        return jsonify({'status': 'error', 'message': 'Ongeldige data'}), 400

    chat_history.append({'username': username, 'message': message})
    return jsonify({'status': 'ok'}), 200

@app.route('/messages', methods=['GET'])
def messages():
    return jsonify(chat_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
