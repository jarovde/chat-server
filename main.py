from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Configuratie
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app)

# Database bestand
DATABASE = 'chat_app.db'

# Functie voor databaseverbinding
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Functie om database in te stellen
def init_db():
    if not os.path.exists(DATABASE):
        with get_db() as conn:
            conn.execute('''CREATE TABLE users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)''')
            conn.execute('''CREATE TABLE messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL,
                            message TEXT NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()

# Initialiseer de database bij opstarten
init_db()

# Admin wachtwoord voor toegang
admin_password = 'admin123'

# Route voor loginpagina
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
            if user:
                session['user'] = username
                return redirect(url_for('chat'))
            else:
                return 'Foutieve gebruikersnaam of wachtwoord', 401
    return render_template('login.html')

# Route voor registratie van gebruikers
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as conn:
            try:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                return 'Gebruikersnaam bestaat al', 409
    return render_template('register.html')

# Route voor het chatvenster
@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['user'])

# Functie om berichten te versturen
@socketio.on('message')
def handle_message(msg):
    with get_db() as conn:
        conn.execute('INSERT INTO messages (username, message) VALUES (?, ?)', (session['user'], msg))
        conn.commit()
    send(msg, broadcast=True)

# Functie voor berichten ophalen
@app.route('/messages', methods=['GET'])
def get_messages():
    with get_db() as conn:
        messages = conn.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 50').fetchall()
    return jsonify([dict(message) for message in messages])

# Functie om uit te loggen
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Admin route
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == admin_password:
            return redirect(url_for('admin_panel'))
        else:
            return 'Foutief wachtwoord', 401
    return render_template('admin_login.html')

# Admin panel route (beheren van berichten en gebruikers)
@app.route('/admin/panel')
def admin_panel():
    return render_template('admin_panel.html')

# Start de Flask app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
