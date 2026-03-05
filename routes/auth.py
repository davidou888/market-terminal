from flask import Blueprint, request, jsonify
from config import get_db
import uuid
import bcrypt

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    conn, cursor = get_db()
    #on fetch juste le username
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    #si le username n'existe pas, on retourne une erreur
    if row is None:
        return jsonify({"ok": False, "error": "user not found"})
    else:
        #on vérifie le mot de passe avec bcrypt (hash)
        if bcrypt.checkpw(password.encode('utf-8'), row[2].encode('utf-8')):
            print(f"[AUTH]: User '{username}' logged in successfully")
            return jsonify({"ok": True, "api_key": row[3]})
        else:
            print(f"[AUTH]: Failed login attempt for user '{username}'")
            return jsonify({"ok": False, "error": "invalid password"})
    
@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    if row is not None:
        conn.close()
        return jsonify({"ok": False, "error": "user already exists"})
    # Generate a random API key (for simplicity, using username + password here, but in production use a secure random generator)
    api_key = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, password_hash, api_key) VALUES (%s, %s, %s)", (username, password_hash, api_key))
    conn.commit()
    conn.close()
    print(f"[AUTH]: Registered new user '{username}'")
    return jsonify({"ok": True, "api_key": api_key})