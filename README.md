# Market Terminal

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)

## What the project does

Market Terminal is a real-time trading game and dashboard built with Flask + Flask-SocketIO, backed by a MySQL order book. It provides:

- live symbol data + historical price series (`/data/<symbol>` from `data/*.csv`)
- REST endpoints for trades, positions, and orders
- secure user authentication (`/login`, `/register`) with API keys
- game engine events (`game_start`, `time_update`, `game_end`)
- order matching and trade log persistence via MySQL

## Why this is useful

- great learning platform for trading systems and matching engines
- simple architecture for rapid prototyping
- supports asynchronous real-time updates
- includes Docker support for consistent local/dev environments
- friendly, extendable codebase for custom market rules

## Quickstart

### prerequisites

- Python 3.11+
- Docker (recommended) or local MySQL
- `pip install -r requirements.txt`

### local launch

1. copy/create `config.env`:

```env
DB_HOST=localhost
DB_USER=*****
DB_PASSWORD=******
DB_NAME=*****
```

2. initialize DB from SQL schema:

```bash
mysql -u root -p < init.sql
```

3. run app:

```bash
python app.py
```

4. open `http://localhost:8000`

### Docker launch

```bash
docker compose up --build
```

- web app: `http://localhost:8000`
- DB: service `db` with init.sql schema seeded

## Key endpoints

- `GET /` → dashboard
- `GET /auth` → login page
- `GET /api/symbols` → list of symbols
- `GET /data/<symbol>` → OHLC history
- `POST /login` → JSON `{username,password}`
- `POST /register` → JSON `{username,password}`
- `GET /get-trades?key=<apikey>&symbol=<sym>`
- `GET /get-pos?key=<apikey>&symbol=<sym>`
- `GET /post-order?key=<apikey>&side=<B|S>&sym=<sym>&price=<p>&vol=<v>`
- `GET /admin/start-game?key=<admin_key>`

## Socket.IO events

- `connect`, `disconnect`
- `game_start`: payload `{symbols, running}`
- `time_update`: payload `{time_left}`
- `game_end`: payload `{running, symbols}`

## Project layout

- app.py: main Flask server + routes + SocketIO init
- auth.py: authentication endpoints
- trade.py: order and position logic
- market.py: game state, countdown, socket events
- game_events.py: socket connect/disconnect events
- `data/*.csv`: market data source
- init.sql: schema + seed
- compose.yaml: Docker Compose config

## Configuration details

- config.py reads `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- admin password constant `ADMIN_PSW` defaults to `admin`
- requirements.txt includes Flask, SocketIO, gevent, yfinance, MySQL connector

## Contributing

1. fork repository
2. create branch `feature/<name>`
3. add tests in tests
4. open PR with summary and testing notes

For full guidelines, add `CONTRIBUTING.md` and link it here.

## Support

- raise GitHub Issues in this repo for bugs/feature requests
- read code comments and log output (`[AUTH]`, `[CONN]`, `[GAME]`, `[SOCKET]`)

## License

See LICENSE in repository root.

