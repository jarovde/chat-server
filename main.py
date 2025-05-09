from flask import Flask, render_template_string, request, jsonify, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Zorg voor een geheime sleutel voor sessies
socketio = SocketIO(app)  # Voeg SocketIO toe aan de app

# Lijst om berichten op te slaan
messages = []

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
    
    <!-- Gebruikersnaam invoerveld -->
    <div id="username-section">
        <label for="username">Enter your username:</label>
        <input type="text" id="username" placeholder="Username">
        <button onclick="setUsername()">Set Username</button>
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

        // Functie om gebruikersnaam in sessie op te slaan
        function setUsername() {
            const username = document.getElementById('username').value;
            if (username) {
                fetch('/set_username', {
                    method: 'POST',
                    body: new URLSearchParams({ username: username }),
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('username-section').style.display = 'none';  // Verberg gebruikersnaam sectie
                    document.getElementById('chat-section').style.display = 'block';  // Toon chat sectie
                    loadMessages();  // Laad berichten
                });
            } else {
                alert("Please enter a username.");
            }
        }

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

        // Ontvang berichten van

