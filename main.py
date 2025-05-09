from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Een lijst voor het opslaan van berichten
messages = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_message():
    message = request.form['message']
    messages.append(message)  # Voeg het bericht toe aan de lijst
    return jsonify(messages)

@app.route('/get_messages')
def get_messages():
    return jsonify(messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

