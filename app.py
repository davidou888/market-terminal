"""
Backend Flask app for the game dashboard.
"""
from gevent import monkey
monkey.patch_all()  # Patch stdlib for gevent compatibility (required for WebSocket support)

from config import get_db
from flask import Flask, render_template, request
from extension import socketio
from datetime import datetime, timedelta
from flask import jsonify
from services.trade import createOrder, getTrades, getPositions





# ── App setup ──────────────────────────────────────────────────────────────────

app = Flask(__name__)
socketio.init_app(app, cors_allowed_origins="*")  # Initialize SocketIO with CORS support
# Import AFTER creating flask app

from sockets import game_events
from sockets import market_events

#enregistrement des blueprint pour auth.py

from routes.auth import auth
# ── Flask routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main dashboard, injecting the initial symbol list."""
    return render_template("dashboard.html", symbols=['GOOGL', 'ETHUSDT', 'BNBUSDT'])

# This route allows the client-side JavaScript to send log messages that will appear in the server console, which is useful for debugging client-side code in environments where you don't have easy
@app.route('/log', methods=['POST'])
def client_log():
    data = request.get_json()
    print(f"[CLIENT] {data.get('message')}", flush=True)
    return '', 204

@app.route("/post-order", methods=["GET"])
def post_order():
    data = {
        "key":   request.args.get("key"),
        "side":  request.args.get("side"),
        "sym":   request.args.get("sym"),
        "price": request.args.get("price"),
        "vol":   request.args.get("vol"),
    }
    result = createOrder(data)
    return jsonify(result)

@app.route("/auth")
def auth_page():
    return render_template("login.html")
#register blueprint for auth routes

app.register_blueprint(auth)
# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=False)
