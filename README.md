# Market Terminal

A real-time market dashboard built with **Flask + Flask-SocketIO** (backend) and a
pure **HTML/CSS/JS** frontend using **ApexCharts** for candlestick rendering.

---

## Architecture

```
Browser  ←──WebSocket (Socket.IO)──→  server.py  ←──WebSocket──→  Finnhub.io
                                           │
                                           └──HTTP (yfinance)──→  Yahoo Finance
```

### server.py

| Component | Purpose |
|---|---|
| `SYMBOLS` | Mutable set of tracked tickers (default: AAPL, AMZN, BINANCE:BTCUSDT) |
| `emit_historical_candles(sym, sid?)` | Downloads OHLCV bars via yfinance and emits `candle` events |
| `on_client_connect()` | Fires when a browser connects; streams historical candles per symbol |
| `on_subscribe_symbol(payload)` | Handles client requests to add new tickers; validates via yfinance |
| `start_finnhub()` | Background thread running the Finnhub WebSocket, auto-reconnects |
| `on_message(ws, msg)` | Parses Finnhub trade ticks and broadcasts `trade` events to all clients |

### dashboard.html

| Component | Purpose |
|---|---|
| Ticker bar | Horizontal scrollable cards — one per tracked symbol — showing live price and % change |
| Candlestick chart | ApexCharts candlestick powered by `candle` events; live trades are merged client-side |
| Favourites panel | Star any symbol to pin it in the sidebar; persisted in `localStorage` |
| Add Symbol panel | Type a ticker (e.g. `TSLA`, `BINANCE:ETHUSDT`) and hit `+` to subscribe |
| Trade log | Live feed of raw ticks from the Finnhub stream |

---

## Socket.IO Events

### Server → Client

| Event | Payload | Description |
|---|---|---|
| `candle` | `{symbol, time, open, high, low, close, volume}` | One 1-min OHLCV bar |
| `trade` | `{symbol, price, volume, time}` | Raw Finnhub tick |
| `history_done` | `{symbol}` | All historical candles for a symbol have been sent |
| `symbol_ack` | `{symbol, ok, error?, already?}` | Response to `subscribe_symbol` |

### Client → Server

| Event | Payload | Description |
|---|---|---|
| `subscribe_symbol` | `{symbol}` | Request to add a new ticker to the live feed |

---

## Installation

```bash
pip install flask flask-socketio websocket-client yfinance pandas
```

### Running

```bash
python server.py
```

Then open **http://localhost:8000** in a browser.

---

## Adding Symbols at Runtime

1. Type a ticker in the **Add Symbol** input (bottom-left sidebar).
2. Supported formats:
   - Stock: `TSLA`, `NVDA`, `MSFT`
   - Crypto (Finnhub): `BINANCE:ETHUSDT`, `BINANCE:SOLUSDT`
3. Click `+` or press **Enter**.
4. The server validates the symbol via yfinance, fetches history, and broadcasts
   `candle` events. A toast notification confirms success or failure.

---

## Favourites

- Click the **★** star icon on any ticker card to toggle it as a favourite.
- Favourites appear in the left sidebar with their latest price and % change.
- Starred symbols persist across page refreshes via `localStorage`.

---

## Candlestick Chart

- Displays **1-minute OHLCV bars** for the active symbol.
- Historical bars come from **yfinance** (last 5 days, 1-min interval).
- Live trades from **Finnhub** are aggregated client-side into the current bar:
  - First tick of a new minute opens a new candle.
  - Subsequent ticks update High, Low, Close, and Volume.
- Switch symbols by clicking any card in the ticker bar or any row in the favourites list.

---

## Configuration

Edit these constants at the top of `server.py`:

| Constant | Default | Purpose |
|---|---|---|
| `API_TOKEN` | `d6ekv…` | Finnhub API token |
| `SYMBOLS` | `["AAPL","AMZN","BINANCE:BTCUSDT"]` | Default symbols on startup |
| `HISTORY_PERIOD` | `"5d"` | yfinance history window |
| `HISTORY_INTERVAL` | `"1m"` | yfinance bar interval |

---

## File Structure

```
.
├── server.py          # Flask backend — Finnhub WS + yfinance history
├── templates/
│   └── dashboard.html # Frontend — candlestick chart, ticker bar, favourites
└── README.md
```

> **Note:** Flask's `render_template` looks for templates in a `templates/`
> sub-directory. Place `dashboard.html` inside `templates/`.
