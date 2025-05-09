from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Een lijst voor het opslaan van berichten
messages = []

# De HTML-code voor de chatinterface
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
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type a message...">
    <button onclick="sendMessage()">Send</button>

    <script>
        // Functie om berichten op te halen van de server
        function loadMessages() {
            fetch('/get_messages')
                .then(response => response.json())
                .then(data => {
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';  // Verwijder oude berichten
                    data.forEach(message => {
                        const messageElement = document.createElement('p');
                        messageElement.textContent = message;
                        messagesDiv.appendChild(messageElement);
                    });
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;  // Scroll naar beneden
                });
        }

        // Functie om een bericht naar de server te sturen
        function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value;
            if (message) {
                fetch('/send', {
                    method: 'POST',
                    body: new URLSearchParams({ message: message }),
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                })
                .then(response => response.json())
                .then(() => {
                    loadMessages();  // Herlaad berichten
                    messageInput.value = '';  // Maak het invoerveld leeg
                });
            }
        }

        // Laad berichten wanneer de pagina wordt geladen
        window.onload = loadMessages;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_content)  # Render de HTML rechtstreeks vanuit een string

@app.route('/send', methods=['POST'])
def send_message():
    message = request.form['message']
    messages.append(message)  # Voeg het bericht toe aan de lijst
    return jsonify(messages)  # Return de lijst van berichten

@app.route('/get_messages')
def get_messages():
    return jsonify(messages)  # Return de lijst van berichten

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
