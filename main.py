from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, escape
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

messages = []
users = {}  # gebruikersnaam: wachtwoord_hash
banned_users = []

ADMIN_USERNAME = 'jarovde'

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chat App</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        #messages { border: 1px solid #ccc; padding: 10px; height: 300px; overflow-y: scroll; }
        input[type="text"], input[type="password"] { width: 80%; padding: 10px; }
        button { padding: 10px; }
    </style>
</head>
<body>
    <h1>Chat App</h1>

    <div id="login-section" style="{{ 'display:none;' if logged_in else '' }}">
        <h2>Login</h2>
        <form action="/login" method="POST">
            <label>Username:</label><br>
            <input type="text" name="username" required><br><br>
            <label>Password:</label><br>
            <input type="password" name="password" required><br><br>
            <button type="submit">Login</button>
        </form>
        <p>No account? <a href="/register">Register</a></p>
    </div>

    <div id="chat-section" style="{{ '' if logged_in else 'display:none;' }}">
        <h2>Welcome, {{ username }}!</h2>
        <div id="messages"></div>
        <input type="text" id="messageInput" placeholder="Message...">
        <button onclick="sendMessage()">Send</button>

        {% if is_admin %}
        <br><br>
        <h3>Ban/unban gebruiker</h3>
        <input type="text" id="banUserInput" placeholder="Username to ban/unban">
        <button onclick="banUser()">Ban</button>
        <button onclick="unbanUser()">Unban</button>
        {% endif %}
        
        <br><br><a href="/logout">Logout</a>
    </div>

    <script src="https://cdn.socket.io/4.0.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        const username = "{{ username }}";

        function loadMessages() {
            fetch('/get_messages')
                .then(res => res.json())
                .then(data => {
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';
                    data.forEach(msg => {
                        const el = document.createElement('p');
                        el.textContent = msg.username + ": " + msg.text;
                        messagesDiv.appendChild(el);
                    });
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                });
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const msg = input.value;
            if (msg) {
                socket.emit('send_message', { username: username, message: msg });
                input.value = '';
            }
        }

        function banUser() {
            const user = document.getElementById('banUserInput').value;
            fetch('/ban_user', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'username=' + encodeURIComponent(user)
            }).then(res => res.json()).then(alert);
        }

        function unbanUser() {
            const user = document.getElementById('banUserInput').value;
            fetch('/unban_user', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'username=' + encodeURIComponent(user)
            }).then(res => res.json()).then(alert);
        }

        socket.on('new_message', () => loadMessages());

        window.onload = function () {
            loadMessages();
            setInterval(loadMessages, 2000);
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return redirect(url_for('chat'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "Username already exists", 400
        users[username] = generate_password_hash(password)
        return redirect(url_for('login'))
    return render_template_string(html_content, logged_in=False, username='', is_admin=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            return redirect(url_for('chat'))
        return "Invalid credentials", 403
    return render_template_string(html_content, logged_in=False, username='', is_admin=False)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = escape(session['username'])
    return render_template_string(html_content,
                                   logged_in=True,
                                   username=username,
                                   is_admin=(username == ADMIN_USERNAME))

@app.route('/get_messages')
def get_messages():
    return jsonify(messages)

@app.route('/ban_user', methods=['POST'])
def ban_user():
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        username_to_ban = request.form['username']
        if username_to_ban not in banned_users:
            banned_users.append(username_to_ban)
            return jsonify({'status': f'{username_to_ban} is banned'})
        return jsonify({'error': 'Already banned'}), 400
    return jsonify({'error': 'Not authorized'}), 403

@app.route('/unban_user', methods=['POST'])
def unban_user():
    if 'username' in session and session['username'] == ADMIN_USERNAME:
        username_to_unban = request.form['username']
        if username_to_unban in banned_users:
            banned_users.remove(username_to_unban)
            return jsonify({'status': f'{username_to_unban} is unbanned'})
        return jsonify({'error': 'User not banned'}), 400
    return jsonify({'error': 'Not authorized'}), 403

@socketio.on('send_message')
def handle_send_message(data):
    username = data['username']
    message = data['message']
    if username in banned_users:
        emit('new_message', {'error': 'You are banned.'}, broadcast=True)
        return
    messages.append({'username': username, 'text': message})
    emit('new_message', {}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
