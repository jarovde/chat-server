from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Zorg voor een geheime sleutel voor sessies
socketio = SocketIO(app)  # Voeg SocketIO toe aan de app

# Lijst om berichten op te slaan
messages = []

# Lijst voor gebruikers en hun wachtwoorden
users = {}  # gebruikersnaam: wachtwoord_hash
banned_users = []

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

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template_string(html_content)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "Username already exists", 400
        users[username] = generate_password_hash(password)  # Wachtwoord veilig opslaan
        return redirect(url_for('login'))
    return render_template_string(html_content)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username], password):
            session['username'] = username  # Sla de gebruikersnaam op in de sessie
            return redirect(url_for('chat'))
        return "Invalid credentials", 403
    return render_template_string(html_content)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template_string(html_content)

@app.route('/send', methods=['POST'])
def send_message():
    if 'username' in session:
        username = session['username']
        message = request.form['message']
        # Controleer of de gebruiker op de banlijst staat
        if username in banned_users:
            return jsonify({'error': 'You are banned from sending messages.'}), 403
        messages.append({'username': username, 'text': message})  # Voeg bericht toe met gebruikersnaam
        return jsonify(messages)
    else:
        return jsonify({'error': 'No username set'}), 400

@app.route('/get_messages')
def get_messages():
    return jsonify(messages)  # Retourneer berichten

@app.route('/ban_user', methods=['POST'])
def ban_user():
    if 'username' in session and session['username'] == ADMIN_USERNAME:  # Alleen admin kan bannen
        username_to_ban = request.form['username']
        if username_to_ban not in banned_users:
            banned_users.append(username_to_ban)  # Voeg toe aan de banlijst
            return jsonify({'status': f'{username_to_ban} has been banned.'})
        else:
            return jsonify({'error': 'User is already banned.'}), 400
    else:
        return jsonify({'error': 'You are not authorized to ban users.'}), 403

@app.route('/unban_user', methods=['POST'])
def unban_user():
    if 'username' in session and session['username'] == ADMIN_USERNAME:  # Alleen admin kan unbannen
        username_to_unban = request.form['username']
        if username_to_unban in banned_users:
            banned_users.remove(username_to_unban)  # Verwijder van de banlijst
            return jsonify({'status': f'{username_to_unban} has been unbanned.'})
        else:
            return jsonify({'error': 'User is not banned.'}), 400
    else:
        return jsonify({'error': 'You are not authorized to unban users.'}), 403

@socketio.on('send_message')
def handle_send_message(data):
    username = data['username']
    message = data['message']
    # Controleer of de gebruiker op de banlijst staat
    if username in banned_users:
        emit('new_message', {'error': 'You are banned from sending messages.'}, broadcast=True)
        return
    messages.append({'username': username, 'text': message})
    emit('new_message', {'messages': messages}, broadcast=True)  # Stuur de nieuwe berichten naar alle clients

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)


