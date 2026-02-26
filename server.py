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
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from gevent import monkey
from gevent.threadpool import ThreadPool

#added a thread pool for yfinance calls to avoid blocking the main event loop, especially when multiple clients connect at once and request historical data for several symbols. 
#The thread pool allows us to run multiple yfinance downloads in parallel without freezing the server.
_thread_pool = ThreadPool(4)
monkey.patch_all()  # Patch stdlib for gevent compatibility (required for WebSocket support)
# ── Configuration ──────────────────────────────────────────────────────────────

# Finnhub WebSocket API token
API_TOKEN = apiKey()

# Default symbols to track on startup.
# Stocks use plain tickers ("AAPL"); crypto uses "EXCHANGE:PAIR" ("BINANCE:BTCUSDT").
SYMBOLS = ["AAPL", "AMZN", "BINANCE:BTCUSDT"]

# How many days of x-min history to load for each symbol when it is first shown.
HISTORY_PERIOD = "5d"
HISTORY_INTERVAL = "1m"

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
        return symbol

def emit_historical_candles(symbol: str, target_sid: str | None = None) -> None:
    # Convert Finnhub symbol format to yfinance format
    # e.g. "BINANCE:BTCUSDT" → "BTC-USD", plain stocks pass through unchanged
    yf_sym = _to_yf_ticker(symbol)

    # Download OHLCV bars from Yahoo Finance
    # HISTORY_PERIOD and HISTORY_INTERVAL are set at the top of the file (e.g. "5d", "1m")
    try:
        # new threaded version of the yfinance download to avoid blocking the main event loop.
        df = _thread_pool.spawn(
            yf.download, 
            yf_sym, 
            period=HISTORY_PERIOD, 
            interval=HISTORY_INTERVAL, 
            progress=False
            ).get()
    except Exception as exc:
        print(f"[yfinance] Failed to download {yf_sym}: {exc}")
        return

    # Nothing came back (market closed, bad ticker, etc.) — bail out silently
    if df.empty:
        print(f"[yfinance] No data returned for {yf_sym}")
        return


#to do: add enum if closed, bad response etc...


    # yfinance sometimes returns a MultiIndex on the columns (e.g. ("Close", "AAPL"))
    # We only ever download one ticker at a time, so we flatten it to plain strings
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # ── Build the candle list in memory first ──────────────────────────────────
    #
    # loop through all rows, collect them into a plain Python
    # list, then send EVERYTHING in a single "history_batch" event.
    # The browser receives one message and processes it all in one go.
    candles = []
    for timestamp, row in df.iterrows():
        candles.append({
            # Milliseconds since epoch — same unit Finnhub uses for live trades,
            # so the chart x-axis stays consistent between history and live data
            "time":   int(timestamp.timestamp() * 1000),

            # OHLCV values — .get() with a fallback to Close handles any rare
            # rows where Open/High/Low are missing (e.g. pre-market stubs)
            "open":   float(row.get("Open",  row.get("Close", 0))),
            "high":   float(row.get("High",  row.get("Close", 0))),
            "low":    float(row.get("Low",   row.get("Close", 0))),
            "close":  float(row.get("Close", 0)),
            "volume": int(row.get("Volume", 0)),
        })

    print(f"[yfinance] Sending batch of {len(candles)} candles for {symbol}")

    # ── Send the batch ─────────────────────────────────────────────────────────
    # Wrap the list in a dict so the client knows which symbol it belongs to
    batch = {"symbol": symbol, "candles": candles}

#to do: passage par ref de batch et candles


    # target_sid is set when sending to one specific browser (on initial connect)
    # If it's None we broadcast to ALL connected clients (when a new symbol is added)
    if target_sid:
        socketio.emit("history_batch", batch, to=target_sid)
        # history_done tells the browser "no more candles coming for this symbol"
        # so it can hide the loading spinner and render the chart
        socketio.emit("history_done", {"symbol": symbol}, to=target_sid)
    else:
        socketio.emit("history_batch", batch)
        socketio.emit("history_done", {"symbol": symbol})


# ── Finnhub WebSocket callbacks ────────────────────────────────────────────────

def on_message(ws: websocket.WebSocketApp, message: str) -> None:
    """Handle incoming messages from Finnhub."""
    data = json.loads(message)
    print("message")
    # Finnhub keeps the connection alive with ping frames.
    if data.get("type") == "ping":
        ws.send(json.dumps({"type": "pong"})) # :))
        return

    if data.get("type") == "trade":
        # Throttle slightly to avoid flooding the client
        #
        #to do: time sleep... vraiment ?
        print("trade")
        time.sleep(0.05)
        for trade in data.get("data", []):
            socketio.emit("trade", {
                "symbol": trade["s"],
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
        time.sleep(5)


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

    socketio.start_background_task(target=_send_history, daemon=True).start() 
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

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Start the Finnhub WebSocket listener in a daemon thread
   # thread = threading.Thread(target=start_finnhub, daemon=True)
   # thread.start()

    # Run Flask-SocketIO (eventlet or threading mode) 
    # !Always run the local server on 8000 port, not 5000, to avoid conflicts with the Finnhub WS thread!
    socketio.run(app, host="0.0.0.0", port=8000, debug=False)
