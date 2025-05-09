from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__)

# Bestandslocatie voor SQLite database
DATABASE = 'users.db'

# Functie om de database te verbinden
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Functie om de database te initialiseren (maak de tabel indien deze nog niet bestaat)
def init_db():
    if not os.path.exists(DATABASE):
        with get_db() as conn:
            conn.execute('''CREATE TABLE users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT UNIQUE NOT NULL,
                            banned BOOLEAN DEFAULT 0)''')
            conn.commit()

init_db()

# Admin wachtwoord voor login
admin_password = "admin123"  # Pas dit wachtwoord aan naar wens

# Route voor login van admin
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data['password'] == admin_password:
        return jsonify(success=True)
    return jsonify(success=False)

# Route om alle gebruikers op te halen
@app.route('/admin/users', methods=['GET'])
def get_users():
    with get_db() as conn:
        users = conn.execute('SELECT * FROM users').fetchall()
    users_list = [{"email": user["email"], "banned": user["banned"]} for user in users]
    return jsonify(users_list)

# Route voor het bannen of deblokkeren van een gebruiker
@app.route('/admin/ban', methods=['POST'])
def ban_user():
    data = request.get_json()
    with get_db() as conn:
        conn.execute('UPDATE users SET banned = ? WHERE email = ?', (data['ban'], data['email']))
        conn.commit()
    return jsonify(success=True)

# Route om een gebruiker toe te voegen
@app.route('/admin/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    with get_db() as conn:
        try:
            conn.execute('INSERT INTO users (email) VALUES (?)', (data['email'],))
            conn.commit()
            return jsonify(success=True)
        except sqlite3.IntegrityError:
            return jsonify(success=False, error="User already exists.")

# Route om een gebruiker te verwijderen
@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json()
    with get_db() as conn:
        conn.execute('DELETE FROM users WHERE email = ?', (data['email'],))
        conn.commit()
    return jsonify(success=True)

# Route om de adminpagina weer te geven (HTML)
@app.route('/admin')
def admin_page():
    return send_from_directory('.', 'admin.html')

if __name__ == '__main__':
    app.run(debug=True)
