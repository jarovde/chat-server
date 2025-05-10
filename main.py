import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

users = {
    "admin": {"password": "admin123", "is_admin": True},
    "user1": {"password": "pass1", "is_admin": False},
    "user2": {"password": "pass2", "is_admin": False},
}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and user['password'] == password:
            session['username'] = username
            session['is_admin'] = user['is_admin']
            return redirect(url_for('admin' if user['is_admin'] else 'chat'))
        return "Foute inloggegevens", 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "Gebruiker bestaat al", 400
        users[username] = {'password': password, 'is_admin': False}
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return "Toegang geweigerd", 403
    return render_template('admin_login.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@socketio.on('message')
def handle_message(data):
    print(f"Ontvangen bericht: {data}")
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    is_local = os.environ.get("FLASK_ENV") != "production"
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
