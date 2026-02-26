# Market Terminal

A real-time market dashboard built with **Flask + Flask-SocketIO** (backend) and a
pure **HTML/CSS/JS** frontend using **QFChart** (via ECharts) for candlestick rendering.

---

## Architecture
```
Browser  ←──WebSocket (Socket.IO)──→  server.py  ←──WebSocket──→  Finnhub.io
                                           │
                                           └──HTTP (yfinance)──→  Yahoo Finance
```

The server uses **gevent** for async I/O. `monkey.patch_all()` is called at startup
to make the standard library gevent-compatible. A `ThreadPool(4)` is used for
parallel yfinance downloads so that multiple symbol requests don't block the event loop.

---

## File Structure
```
.
├── server.py               # Flask backend — Finnhub WS + yfinance history + disk cache
├── templates/
│   └── dashboard.html      # Frontend HTML — chart, ticker bar, favourites, trade log
├── static/
│   ├── css/
│   │   └── dashboard.css   # Full UI theme (CSS custom properties, grid layout)
│   └── js/
│       └── dashboard.js    # Frontend logic — Socket.IO events, QFChart, favourites
├── key.py                  # Returns Finnhub API token (gitignored)
├── requirements.txt
├── Dockerfile
├── compose.yaml
└── config.env              # Environment variables for Docker Compose
```

> **Note:** `key.py` is gitignored. Create it manually:
> ```python
> def apiKey(): return "your_finnhub_token_here"
> ```

---

## Installation (local)
```bash
pip install flask flask-socketio websocket-client yfinance pandas gevent gevent-websocket
```

### Running locally
```bash
python server.py
```
Open **http://localhost:8000**.

### Running with Docker
```bash
docker compose up --build
```
App available at **http://localhost:8000**.

Docker Compose starts two services:
- **app** — the Flask/gevent server (port 8000)
- **db** — a MySQL 8 instance (future persistence; not yet wired into `server.py`)

Environment variables are read from `config.env`:
```
MYSQL_ROOT_PASSWORD=my-secret-pw
MYSQL_DATABASE=my_database
DB_USER=root
```

---

## Server — `server.py`

### Key constants

| Constant | Default | Purpose |
|---|---|---|
| `SYMBOLS` | `["AAPL","AMZN","BINANCE:BTCUSDT"]` | Default symbols loaded on startup |
| `HISTORY_PERIOD` | `"1y"` | yfinance history window |
| `HISTORY_INTERVAL` | `"1d"` | yfinance bar interval (daily candles) |
| `BATCH_SIZE` | `400` | Candles sent per `history_batch` emission |
| `MAX_CANDLES_SERVER` | `4000` | Max candles kept per symbol in the disk cache |
| `CACHE_TTL_HOURS` | `4` | Disk cache expiry (hours) |
| `CACHE_DIR` | `/tmp/market_cache` | Directory for pickle cache files |

### Components

| Component | Purpose |
|---|---|
| `_to_yf_ticker(sym)` | Converts Finnhub format to yfinance (`BINANCE:BTCUSDT` → `BTC-USD`) |
| `_load_cache(sym)` / `_save_cache(sym, candles)` | Pickle-based per-symbol disk cache with TTL |
| `_append_candle(sym, candle)` | Merges a live tick into the disk cache (FIFO, 1-min bars) |
| `emit_historical_candles(sym, sid?)` | Loads history (cache or yfinance), emits `history_batch` events in chunks |
| `on_client_connect()` | Streams historical candles on connect; lazily starts the Finnhub thread on first connection |
| `on_subscribe_symbol(payload)` | Validates + adds new tickers; broadcasts to all clients |
| `start_finnhub()` | Background task running the Finnhub WebSocket with auto-reconnect |
| `on_message(ws, msg)` | Parses Finnhub trade ticks, broadcasts `trade` events, updates disk cache |

### Disk cache

Historical OHLCV data is cached to `/tmp/market_cache/<symbol>.pkl` on first fetch and considered valid for `CACHE_TTL_HOURS` (4 h). Live Finnhub ticks are merged into the cache in real time via `_append_candle()`, keeping the cache hot between restarts without a full yfinance re-download.

---

## Socket.IO Events

### Server → Client

| Event | Payload | Description |
|---|---|---|
| `history_batch` | `{symbol, candles: [{time,open,high,low,close,volume}, …]}` | One chunk of historical OHLCV bars (up to `BATCH_SIZE` candles) |
| `history_done` | `{symbol}` | All historical candles for a symbol have been sent |
| `trade` | `{symbol, price, volume, time}` | Raw Finnhub tick |
| `symbol_ack` | `{symbol, ok, error?, already?}` | Response to `subscribe_symbol` |

### Client → Server

| Event | Payload | Description |
|---|---|---|
| `subscribe_symbol` | `{symbol}` | Request to add a new ticker to the live feed |

---

## Frontend — `dashboard.js` / `dashboard.html`

### Per-symbol state (`history[sym]`)
```js
{
  candles:    [ { x: ms, o, h, l, c, v }, … ],  // sorted ascending
  lastTrade:  price,                              // latest tick price
  openPrice:  price,                              // first price seen (for % change)
}
```

`MAX_CANDLES = 500` — oldest candles are dropped from the left when the limit is reached.

### Chart

Rendered by **QFChart** (ECharts wrapper). History batches are accumulated in memory without redrawing each chunk. A single `renderChart()` runs after `history_done`. Live ticks update the current bar via `qfChart.updateData()`.

### Components

| Component | Purpose |
|---|---|
| Ticker bar | Scrollable cards — one per symbol — live price + % change |
| Candlestick chart | QFChart powered by `history_batch` + `trade` events |
| Favourites panel | ★ pins a symbol to the sidebar; persisted in `localStorage` |
| Add Symbol panel | Type a ticker + hit `+` or Enter to subscribe |
| Trade log | Last 60 raw Finnhub ticks across all symbols |
| Toast notifications | Top-right popups confirming symbol add success / failure |
| Clock | Live clock with browser local timezone via `Intl.DateTimeFormat` |

### Debug logging

`debugLog(msg)` POSTs to `/log` → server prints `[CLIENT] …` to stdout. Useful for inspecting client state from the server console.

---

## Adding Symbols at Runtime

1. Type a ticker in the **Add Symbol** input (bottom of the left sidebar).
2. Supported formats — Stock: `TSLA`, `NVDA` · Crypto: `BINANCE:ETHUSDT`, `BINANCE:SOLUSDT`
3. Click `+` or press **Enter**.
4. The server validates via yfinance, fetches history, caches it, and broadcasts `history_batch` to **all** clients. A toast confirms success or failure.
5. If the symbol is already tracked, history is re-sent to the requesting client only (`already: true`).

---

## Favourites

- Click ★ on any ticker card to toggle.
- Pinned symbols appear in the left sidebar with latest price and % change.
- Persisted across refreshes via `localStorage` (key: `mkt_favourites`).

---

## Deployment (Docker)
```bash
docker compose up --build
```

Gunicorn is configured with the `geventwebsocket` worker, 1 worker process, 120 s timeout, and `/dev/shm` as the worker tmp dir.

> Only **one Gunicorn worker** (`-w 1`) is used. Socket.IO requires sticky sessions or a single worker when no message broker (e.g. Redis) is configured. Scale horizontally only after adding a Redis Socket.IO adapter.
