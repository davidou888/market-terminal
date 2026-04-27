# market-terminal

> A real-time competitive trading simulation platform. Place orders, match trades, and climb the leaderboard — all within a timed game session.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3%2B-lightgrey?style=flat-square)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](./LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue?style=flat-square)](./compose.yaml)

---

## What is this?

**market-terminal** is a web-based trading game where participants compete in real time against a shared order book. An admin starts a timed session, symbols are revealed, and players place limit or market orders through a live dashboard. Trades are matched by a price-time priority engine, positions and balances update instantly, and a leaderboard tracks who is winning.

It is designed as a learning platform for trading systems — the matching engine, order book structure, and position accounting are real implementations, not stubs.

---

## Features

- **Live order book** — bids and asks rendered in real time via WebSocket
- **Price-time priority matching engine** — handles partial fills, market orders, and remainder persistence
- **Candlestick chart** — historical price series per symbol loaded from CSV
- **Portfolio panel** — live positions with average price and P&L
- **Leaderboard** — ranks all players by portfolio value during the session
- **Timed game sessions** — admin-triggered countdown with `game_start` / `game_end` broadcast events
- **Secure auth** — bcrypt password hashing, UUID v4 API keys
- **Dark / light theme toggle**
- **Docker Compose** — one command to run the full stack

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask, Flask-SocketIO |
| Async runtime | gevent |
| Database | MySQL 8 |
| Frontend | Vanilla JS, ECharts, Socket.IO client |
| Auth | bcrypt, UUID v4 |
| Container | Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (recommended), **or** a local MySQL 8 instance

---

### Option A — Docker (recommended)

```bash
git clone <repo-url>
cd market-terminal

# Copy and fill in the environment file
cp config.env.example config.env   # edit DB_* and ADMIN_KEY values

docker compose up --build
```

Open `http://localhost:8000`.

---

### Option B — Local setup

```bash
git clone <repo-url>
cd market-terminal

python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Initialize the database:

```bash
mysql -u root -p < init.sql
```

Set environment variables (see [Configuration](#configuration)), then run:

```bash
python app.py
```

Open `http://localhost:8000`.

---

## Configuration

Create a `config.env` file at the project root (never commit this file):

```env
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=trading
ADMIN_KEY=choose-a-strong-secret-key
```

| Variable | Description |
|---|---|
| `DB_HOST` | MySQL host |
| `DB_USER` | MySQL user |
| `DB_PASSWORD` | MySQL password |
| `DB_NAME` | Database name (default: `trading`) |
| `ADMIN_KEY` | Secret key required to call admin endpoints |

> **Never use default or example credentials in production.**

---

## Project Structure

```
market-terminal/
├── app.py                  # Flask app, routes, entry point
├── config.py               # DB connection, env variable loading
├── security.py             # Input validation (UUID v4 enforcement)
├── extension.py            # SocketIO instance (avoids circular imports)
├── init.sql                # DB schema and seed data
├── compose.yaml            # Docker Compose config
├── requirements.txt
│
├── models/
│   └── order.py            # Order, Trade, Position, OrderBook classes
│
├── services/
│   ├── trade.py            # Validation helpers and order orchestration
│   └── market.py           # Game state, countdown, socket broadcasts
│
├── routes/
│   └── auth.py             # /login and /register blueprints
│
├── sockets/
│   ├── game_events.py      # connect / disconnect handlers
│   └── market_events.py    # market socket event handlers
│
├── templates/
│   ├── dashboard.html      # Main trading UI
│   └── login.html          # Auth page
│
├── static/
│   ├── css/dashboard.css
│   └── js/dashboard.js
│
└── data/
    └── <SYMBOL>.csv        # Historical price data per symbol
```

---

## API Reference

### Auth

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/login` | `{username, password}` | Returns `{ok, api_key}` |
| `POST` | `/register` | `{username, password}` | Creates user, returns `{ok, api_key}` |

### Trading

| Method | Endpoint | Params | Description |
|---|---|---|---|
| `GET` | `/get-trades` | `key`, `symbol` (optional) | List open orders |
| `GET` | `/get-pos` | `key`, `symbol` (optional) | List user positions |
| `GET` | `/post-order` | `key`, `side`, `sym`, `price`, `vol` | Place an order |

> `side`: `B` (buy) or `S` (sell). Leave `price` empty for a market order.

### Market data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/symbols` | List of active symbols |
| `GET` | `/data/<symbol>` | Historical OHLC series from CSV |

### Admin

| Method | Endpoint | Params | Description |
|---|---|---|---|
| `GET` | `/admin/start-game` | `key` (admin key) | Starts a new 10-minute game session |

---

## WebSocket Events

All events are broadcast to all connected clients via Socket.IO.

| Event | Direction | Payload | Description |
|---|---|---|---|
| `connect` | client → server | — | Client joins |
| `disconnect` | client → server | — | Client leaves |
| `game_start` | server → client | `{symbols, running}` | Session started |
| `time_update` | server → client | `{time_left}` | Countdown tick (every second) |
| `game_end` | server → client | `{running, symbols}` | Session ended with final prices |
| `made_trade` | server → client | `{symbol, quantity, price}` | Trade executed |

---

## Running Tests

```bash
pytest -q
```

Tests live in `tests/`. Coverage is currently focused on the matching engine and order validation. Contributions expanding endpoint and WebSocket test coverage are welcome.

---

## Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests where relevant
4. Open a pull request with a short summary and testing notes

Please do not commit `config.env`, credentials, or generated data files.

---

## License

[MIT](./LICENSE)
