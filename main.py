import sqlite3
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Zorg voor een geheime sleutel voor sessies
socketio = SocketIO(app)  # Voeg SocketIO toe aan de app

# Admin gebruikersnaam
ADMIN_USERNAME = 'jarovde'

# HTML-template voor de frontend
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Application</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        #messages {
            border: 1px solid #ccc;
            padding: 10px;
            height: 300px;
            overflow-y: scroll;
        }
        input[type="text"] {
            width: 80%;
            padding: 10px;
        }
        button {
            padding: 10px;
        }
    </style>
</head>
<body>
    <h1>Chat Application</h1>
    
    <!-- Login sectie -->
    <div id="login-section">
        <h2>Login</h2>
        <form action="/login" method="POST">
            <label for="username">Username:</label><br>
            <input type="text" id="username" name="username" required><br><br>
            <label for="password">Password:</label><br>
            <input type="password" id="password" name="password" required><br><br>
            <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <a href="/register">Register here</a></p>
    </div>

    <!-- Register sectie -->
    <div id="register-section" style="display:none;">
        <h2>Register</h2>
        <form action="/register" method="POST">
            <label for="new_username">Username:</label><br>
            <input type="text" id="new_username" name="username" required><br><br>
            <label for="new_password">Password:</label><br>
            <input type="password" id="new_password" name="password" required><br><br>
            <button type="submit">Register</button>
        </form>
        <p>Already have an account? <a href="/">Login here</a></p>
    </div>

    <div id="chat-section" style="display:none;">
        <h2>Chat Room</h2>
        <div id="messages"></div>
        <input type="text" id="messageInput" placeholder="Type a message...">
        <button onclick="sendMessage()">Send</button>
    </div>

    <div id="admin-panel" style="display:none;">
        <h2>Admin Control Panel</h2>
        <h3>Ban a user</h3>
        <form action="/ban_user" method="POST">
            <label for="ban_username">Username:</label><br>
            <input type="text" id="ban_username" name="username" required><br><br>
            <button type="submit">Ban User</button>
        </form>
        <h3>Unban a user</h3>
        <form action="/unban_user" method="POST">
            <label for="unban_username">Username:</label><br>
            <input type="text" id="unban_username" name="username" required><br><br>
            <button type="submit">Unban User</button>
        </form>
        <h3>Manage Users</h3>
        <ul>
            {% for user in users %}
                <li>{{ user[0] }} - <a href="/delete_user/{{ user[0] }}">Delete</a></li>
            {% endfor %}
        </ul>
    </div>

    <script src="https://cdn.socket.io/4.0.1/socket.io.min.js"></script>
    <script>
        const socket = io.connect('http://' + document.domain + ':' + location.port);

        // Functie om berichten op te halen van de server
        function loadMessages() {
            fetch('/get_messages')
                .then(response => response.json())
                .then(data => {
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';  // Verwijder oude berichten
                    data.forEach(message => {
                        const messageElement = document.createElement('p');
                        messageElement.textContent = message.username + ": " + message.text;
                        messagesDiv.appendChild(messageElement);
                    });
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;  // Scroll naar beneden
                });
        }

        // Functie om een bericht naar de server te sturen
        function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const username = document.getElementById('username').value;
            const message = messageInput.value;
            if (message && username) {
                socket.emit('send_message', { username: username, message: message });
                messageInput.value = '';  // Maak het invoerveld leeg
            } else {
                alert("Please enter a message.");
            }
        }

        // Ontvang berichten van de server in real-time
        socket.on('new_message', function(data) {
            loadMessages();
        });

        // Laad berichten wanneer de pagina wordt geladen
        window.onload = function() {
            loadMessages();
            setInterval(loadMessages, 2000);  // Haal elke 2 seconden nieuwe berichten op
        };
    </script>
</body>
</html>
"""

def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ips (ip TEXT PRIMARY KEY, username TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned (username TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ip = request.remote_addr
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT * FROM ips WHERE ip=?", (ip,))
        if c.fetchone():
            conn.close()
            return "This device already registered an account.", 403
        username = request.form['username']
        password = request.form['password']
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.fetchone():
            conn.close()
            return "Username already exists", 400
        c.execute("INSERT INTO users VALUES (?, ?)", (username, generate_password_hash(password)))
        c.execute("INSERT INTO ips VALUES (?, ?)", (ip, username))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template_string(html_content)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], password):
        session['username'] = username
        return redirect('/')
    return "Invalid credentials", 403

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template_string(html_content)

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template_string(html_content)

@app.route('/ban_user', methods=['POST'])
def ban_user():
    if session.get('username') == ADMIN_USERNAME:
        username = request.form['username']
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO banned VALUES (?)", (username,))
        conn.commit()
        conn.close()
        return jsonify({'status': f'{username} banned'})
    return jsonify({'error': 'unauthorized'}), 403

@app.route('/unban_user', methods=['POST'])
def unban_user():
    if session.get('username') == ADMIN_USERNAME:
        username = request.form['username']
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("DELETE FROM banned WHERE username=?", (username,))
        conn.commit()
        conn.close()
        return jsonify({'status': f'{username} unbanned'})
    return jsonify({'error': 'unauthorized'}), 403

@socketio.on('send_message')
def handle_send_message(data):
    username = data['username']
    message = data['message']
    # Controleer of de gebruiker op de banlijst staat
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM banned WHERE username=?", (username,))
    if c.fetchone():
        emit('new_message', {'error': 'You are banned from sending messages.'}, broadcast=True)
        return
    conn.close()

    messages.append({'username': username, 'text': message})
    emit('new_message', {'messages': messages}, broadcast=True)  # Stuur de nieuwe berichten naar alle clients

if __name__ == "__main__":
    init_db()
    socketio.run(app, debug=True)

