from extension import socketio   # ← import depuis extensions, pas app
from flask_socketio import emit
from flask import request
from services.trade import createOrder


@socketio.on('connect')
def on_connect():
    print(f"[SOCKET] Client connected: {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"[SOCKET] Client disconnected: {request.sid}")
        