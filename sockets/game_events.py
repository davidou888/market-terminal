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

@socketio.on('buy')
def on_buy(data):
    data["side"] = "B"
    result = createOrder(data)
    if result:
        emit("trade_result", {"ok": True, "msg": result})
    else:
        emit("trade_result", {"ok": False, "msg": "Failed to create order"})

@socketio.on('sell')
def on_sell(data):
    data["side"] = "S"
    result = createOrder(data)
    if result:
        emit("trade_result", {"ok": True, "msg": result})
    else:
        emit("trade_result", {"ok": False, "msg": "Failed to create order"})

        