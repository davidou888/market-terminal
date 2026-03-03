"""
server.py — Market Feed Backend
================================
Flask + Flask-SocketIO server that:
  1. Streams live trades from Finnhub WebSocket for each tracked symbol.
  2. Emits historical OHLCV candles (1-min bars via yfinance) when a client connects
     or requests a new symbol, so the candlestick chart is pre-populated.
  3. Handles dynamic symbol subscription:  the client can emit a `subscribe_symbol`
     event at any time; the server validates the ticker, fetches history, and adds it
     to the live Finnhub stream.

Socket events (server → client)
--------------------------------
  candle  {symbol, open, high, low, close, volume, time}   — 1-min OHLCV bar
  trade   {symbol, price, volume, time}                    — raw tick (live only)
  symbol_ack  {symbol, ok, error}                          — confirmation of a
                                                             `subscribe_symbol` request

Socket events (client → server)
--------------------------------
  subscribe_symbol  {symbol}   — add a new ticker to track

Dependencies:  flask, flask-socketio, websocket-client, yfinance, pandas
"""

from gevent import monkey
monkey.patch_all()  # Patch stdlib for gevent compatibility (required for WebSocket support)


import json
import threading
import time
from key import apiKey
import pandas as pd 
import websocket
import yfinance as yf
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from gevent import monkey
from gevent.threadpool import ThreadPool
import os
import pickle
from datetime import datetime, timedelta


from exchange import getTrades, getPositions, createOrder

# Dossier où stocker les fichiers cache (un fichier .pkl par symbol)
CACHE_DIR = "/tmp/market_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Durée de validité du cache (au-delà, on re-fetch yfinance)
CACHE_TTL_HOURS = 4

# Nombre maximum de candles à garder par symbol en mémoire serveur
MAX_CANDLES_SERVER = 4000

#added a thread pool for yfinance calls to avoid blocking the main event loop, especially when multiple clients connect at once and request historical data for several symbols. 
#The thread pool allows us to run multiple yfinance downloads in parallel without freezing the server.
_thread_pool = ThreadPool(4)
# ── Configuration ──────────────────────────────────────────────────────────────

# Finnhub WebSocket API token
API_TOKEN = apiKey()

# Default symbols to track on startup.
# Stocks use plain tickers ("AAPL"); crypto uses "EXCHANGE:PAIR" ("BINANCE:BTCUSDT").
SYMBOLS = ["AAPL", "AMZN", "BINANCE:BTCUSDT"]

# How many days of x-min history to load for each symbol when it is first shown.
HISTORY_PERIOD = "1y"
HISTORY_INTERVAL = "1d"

BATCH_SIZE = 400  # Number of candles to send in each "history_batch" message (tune for performance vs. UI responsiveness)


# ── App setup ──────────────────────────────────────────────────────────────────

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Mutable set of currently tracked symbols (protected by a lock because the
# Finnhub WS thread and SocketIO handlers run concurrently).
_symbols_lock = threading.Lock()
_active_symbols: set = set(SYMBOLS)

# Reference to the live Finnhub WebSocketApp so we can send new `subscribe`
# messages after the initial connection.
_finnhub_ws: websocket.WebSocketApp | None = None


# ── Historical data helpers ────────────────────────────────────────────────────



def _to_yf_ticker(symbol: str) -> str:
    """Convert a Finnhub symbol to a yfinance ticker.

    Finnhub uses "BINANCE:BTCUSDT"; yfinance uses "BTC-USD".
    For plain stock tickers the name passes through unchanged.
    """
    if ":" in symbol:
        #parse the exchange and pair from the symbol, then convert to yfinance format
        print(f"[yfinance] Detected crypto symbol {symbol}")
        print(f"[yfinance] Converting {symbol} to yfinance format…")
        exchange_code = symbol.split(":")[0]
        pair = symbol.split(":")[1]          
        base = pair.replace("USDT", "") 
        return f"{base}-USD"
        return symbol
    else:
        print(f"[yfinance] Detected stock symbol {symbol}")
        return symbol
def _cache_path(symbol: str) -> str:
    safe = symbol.replace(":", "_")
    return os.path.join(CACHE_DIR, f"{safe}.pkl")

def _load_cache(symbol: str) -> list | None:
    """Charge le cache d'un symbol. Retourne None si absent ou expiré."""
    path = _cache_path(symbol)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        # Vérifie la fraîcheur
        if datetime.now() - data["saved_at"] > timedelta(hours=CACHE_TTL_HOURS):
            print(f"[cache] Expired for {symbol}")
            return None
        print(f"[cache] Hit for {symbol} — {len(data['candles'])} candles")
        return data["candles"]
    except Exception as e:
        print(f"[cache] Load error for {symbol}: {e}")
        return None

def _save_cache(symbol: str, candles: list) -> None:
    """Sauvegarde la liste de candles sur disque."""
    # Garde seulement les MAX_CANDLES_SERVER plus récentes
    candles = candles[-MAX_CANDLES_SERVER:]
    try:
        with open(_cache_path(symbol), "wb") as f:
            pickle.dump({"saved_at": datetime.now(), "candles": candles}, f)
        print(f"[cache] Saved {len(candles)} candles for {symbol}")
    except Exception as e:
        print(f"[cache] Save error for {symbol}: {e}")

def _append_candle(symbol: str, candle: dict) -> None:
    """
    Ajoute une candle live au cache disque de façon FIFO :
    si on dépasse MAX_CANDLES_SERVER, la plus vieille est supprimée.
    Appelé à chaque trade reçu de Finnhub.
    """
    cached = _load_cache(symbol)
    if cached is None:
        return  # Pas de cache existant, on ne crée pas depuis des ticks live
    
    # Cherche si la candle (même timestamp) existe déjà → update
    bk = (candle["time"] // 60000) * 60000  # arrondi à la minute
    for i, c in enumerate(cached):
        if c["time"] == bk:
            cached[i]["high"]   = max(cached[i]["high"],  candle["price"])
            cached[i]["low"]    = min(cached[i]["low"],   candle["price"])
            cached[i]["close"]  = candle["price"]
            cached[i]["volume"] += candle["volume"]
            _save_cache(symbol, cached)
            return
    
    # Nouvelle candle : append + trim FIFO
    cached.append({
        "time":   bk,
        "open":   candle["price"],
        "high":   candle["price"],
        "low":    candle["price"],
        "close":  candle["price"],
        "volume": candle["volume"],
    })
    _save_cache(symbol, cached)  # _save_cache tronque à MAX_CANDLES_SERVER

def emit_historical_candles(symbol: str, target_sid: str | None = None,
                            period: str = HISTORY_PERIOD, 
                            interval: str = HISTORY_INTERVAL) -> None:
    # Convert Finnhub symbol format to yfinance format
    # e.g. "BINANCE:BTCUSDT" → "BTC-USD", plain stocks pass through unchanged
    yf_sym = _to_yf_ticker(symbol)

    # Download OHLCV bars from Yahoo Finance
    # HISTORY_PERIOD and HISTORY_INTERVAL are set at the top of the file (e.g. "5d", "1m")
    candles = _load_cache(symbol)

    if candles is None:
        # Cache absent ou expiré → fetch yfinance
        try:
            df = _thread_pool.spawn(
                yf.download,
                yf_sym,
                period=period,
                interval=interval,
                progress=False
            ).get()
        except Exception as exc:
            print(f"[yfinance] Failed to download {yf_sym}: {exc}")
            return

        if df.empty:
            print(f"[yfinance] No data returned for {yf_sym}")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        time_col = "Datetime" if "Datetime" in df.columns else "Date"

        candles = []
        for _, row in df.iterrows():
            candles.append({
                "time":   int(pd.Timestamp(row[time_col]).timestamp() * 1000),
                "open":   float(row["Open"]),
                "high":   float(row["High"]),
                "low":    float(row["Low"]),
                "close":  float(row["Close"]),
                "volume": int(row["Volume"]),
            })

        # Sauvegarde dans le cache (trimé à MAX_CANDLES_SERVER)
        _save_cache(symbol, candles)
        candles = candles[-MAX_CANDLES_SERVER:]

    print(f"[history] Sending {len(candles)} candles for {symbol}")
    # ── Send the batch ─────────────────────────────────────────────────────────
    # Wrap the list in a dict so the client knows which symbol it belongs to
    batch = {"symbol": symbol, "candles": candles}

#to do: passage par ref de batch et candles

    for i in range(0, len(candles), BATCH_SIZE):
          # Send in batches of 100 candles to avoid overwhelming the client
        chunk = candles[i:i+BATCH_SIZE]
        batch = {"symbol": symbol, "candles": chunk}
        if target_sid:
            socketio.emit("history_batch", batch, to=target_sid)
            print(f"[history] Sent batch of {len(chunk)} candles for {symbol} to sid={target_sid}") 
        else:
            socketio.emit("history_batch", batch)
            print(f"[history] Broadcasted batch of {len(chunk)} candles for {symbol} to all clients")
        socketio.sleep(0)  # Yield to the event loop to keep the server responsive

    # target_sid is set when sending to one specific browser (on initial connect)
    # If it's None we broadcast to ALL connected clients (when a new symbol is added)

    if target_sid:
        socketio.emit("history_done", {"symbol": symbol}, to=target_sid)
    else:
        socketio.emit("history_done", {"symbol": symbol})


# ── Finnhub WebSocket callbacks ────────────────────────────────────────────────

def on_message(ws: websocket.WebSocketApp, message: str) -> None:
    """Handle incoming messages from Finnhub."""
    data = json.loads(message)
    # Finnhub keeps the connection alive with ping frames.
    if data.get("type") == "ping":
        ws.send(json.dumps({"type": "pong"})) # :))
        return

    if data.get("type") == "trade":
        # Throttle slightly to avoid flooding the client
        #
        #to do: time sleep... vraiment ?
        #time.sleep(2)
        for trade in data.get("data", []):
            socketio.emit("trade", {
                "symbol": trade["s"],
                "price":  trade["p"],
                "volume": trade["v"],
                "time":   trade["t"],
            })
        # Met à jour le cache disque avec la nouvelle candle (FIFO)
            _append_candle(trade["s"], {
                "price":  trade["p"],
                "volume": trade["v"],
                "time":   trade["t"],
            })


def on_error(ws: websocket.WebSocketApp, error: Exception) -> None:
    print(f"[Finnhub error] {error}")


def on_close(ws: websocket.WebSocketApp, code: int, msg: str) -> None:
    global _finnhub_ws
    _finnhub_ws = None
    print(f"[Finnhub closed] {code} {msg}")


def on_open(ws: websocket.WebSocketApp) -> None:
    """Subscribe to all currently tracked symbols once the WS connects."""
    global _finnhub_ws
    _finnhub_ws = ws
    print("[Finnhub] Connected — subscribing to symbols…")
    with _symbols_lock:
        for symbol in _active_symbols:
            ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))

_finnhub_started = False
def start_finnhub() -> None:
    """Run the Finnhub WebSocket in a background thread; auto-reconnects on failure."""
    print("[Finnhub] Thread started")
    delay = 5
    while True:
        ws = websocket.WebSocketApp(
            f"wss://ws.finnhub.io?token={API_TOKEN}",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        ws.run_forever(ping_interval=30, ping_timeout=10)
        print("[Finnhub] Reconnecting in 5 s…")
        time.sleep(delay)


# ── SocketIO event handlers ────────────────────────────────────────────────────

@socketio.on("connect")
def on_client_connect(auth=None) -> None:
    """When a browser connects, stream historical candles for every tracked symbol."""
   
    global _finnhub_started
    if not _finnhub_started:
        _finnhub_started = True
        socketio.start_background_task(start_finnhub)


    sid = request.sid
    print(f"[Client connected] sid={sid} — sending historical candles…")

    with _symbols_lock:
        symbols_snapshot = list(_active_symbols)

    # Emit history in a background thread to avoid blocking the event loop
    def _send_history():
        for sym in symbols_snapshot:
            emit_historical_candles(sym, target_sid=sid)

    socketio.start_background_task(_send_history)
    #fixed a bug where the background task was not marked as daemon, which could cause the server to hang on shutdown if a client was connected and receiving historical data.


@socketio.on("subscribe_symbol")
def on_subscribe_symbol(payload: dict) -> None:
    """Client requests adding a new symbol to the live feed.

    Expected payload: {"symbol": "TSLA"}
    The server validates that yfinance can find data for the ticker, then:
      - adds it to _active_symbols
      - sends a Finnhub subscribe message (if connected)
      - broadcasts historical candles for all clients
      - sends a symbol_ack confirmation
    """
    
    sid = request.sid

    #Cleans the input and rejects empty strings immediately.
    raw_symbol: str = payload.get("symbol", "").strip().upper()
    if not raw_symbol:
        socketio.emit("symbol_ack", {"symbol": raw_symbol, "ok": False,
                                     "error": "Empty symbol"}, to=sid)
        return

    with _symbols_lock:
        already_tracked = raw_symbol in _active_symbols

    if already_tracked:
        # Re-send history to the requesting client so it can refresh
        threading.Thread(
            target=emit_historical_candles,
            args=(raw_symbol, sid),
            daemon=True,
        ).start()
        socketio.emit("symbol_ack", {"symbol": raw_symbol, "ok": True,
                                     "already": True}, to=sid)
        return

    # Validate via yfinance before committing
    yf_sym = _to_yf_ticker(raw_symbol)
    try:
        test = yf.download(yf_sym, period="1d", interval="1m", progress=False)
        if test.empty:
            raise ValueError("Empty dataset")
    except Exception as exc:
        socketio.emit("symbol_ack", {"symbol": raw_symbol, "ok": False,
                                     "error": str(exc)}, to=sid)
        return

    # All good — register the new symbol
    with _symbols_lock:
        _active_symbols.add(raw_symbol)

    # Subscribe on the live Finnhub stream if the WS is open
    if _finnhub_ws is not None:
        try:
            _finnhub_ws.send(json.dumps({"type": "subscribe", "symbol": raw_symbol}))
        except Exception as exc:
            print(f"[Finnhub] Could not subscribe to {raw_symbol}: {exc}")

    # Broadcast history for the new symbol to ALL connected clients
    def _broadcast_new():
        emit_historical_candles(raw_symbol)

    threading.Thread(target=_broadcast_new, daemon=True).start()

    socketio.emit("symbol_ack", {"symbol": raw_symbol, "ok": True}, to=sid)
    print(f"[subscribe_symbol] Added {raw_symbol}")

# ── Flask routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main dashboard, injecting the initial symbol list."""
    return render_template("dashboard.html", symbols=list(_active_symbols))

# This route allows the client-side JavaScript to send log messages that will appear in the server console, which is useful for debugging client-side code in environments where you don't have easy
@app.route('/log', methods=['POST'])
def client_log():
    data = request.get_json()
    print(f"[CLIENT] {data.get('message')}", flush=True)
    return '', 204



@app.route("/get-trades", methods=["GET"])
def get_trades():
    key = request.args.get("key")
    symbol = request.args.get("symbol")
    if not key:
        return jsonify({"error": "Missing key parameter"}), 400

    result = getTrades(key, symbol)

    return jsonify(result)



@app.route("/get-pos", methods=["GET"])
def get_pos():
    key = request.args.get("key")
    symbol = request.args.get("symbol")
    if not key:
        return jsonify({"error": "Missing key parameter"}), 400
    
    result = getPositions(key, symbol)
  
    return jsonify(result)

@app.route("/post-order", methods=["POST", "GET"])
def newOrder():
    orderDict = request.args

    result = createOrder(orderDict)
    return jsonify(result)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    # Start the Finnhub WebSocket listener in a daemon thread
   # thread = threading.Thread(target=start_finnhub, daemon=True)
   # thread.start()

    # Run Flask-SocketIO (eventlet or threading mode) 
    # !Always run the local server on 8000 port, not 5000, to avoid conflicts with the Finnhub WS thread!
    socketio.run(app, host="0.0.0.0", port=8000, debug=False)
