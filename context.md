# Project Context - market-terminal

## Purpose
`market-terminal` is a Python trading simulation platform with realtime updates.
Primary goal: provide an educational and competitive trading environment with order placement, matching, positions, and timed game sessions.

## Current Stack
- Backend: Flask, Flask-SocketIO, gevent
- Data: MySQL
- Frontend: server-rendered templates + JavaScript dashboard
- Runtime: local Python and Docker Compose

## Core Architecture
- Entrypoint: `app.py`
- Trade orchestration: `services/trade.py`
- Matching and trading domain logic: `models/order.py`
- Session/game control: `services/market.py`
- Auth routes: `routes/auth.py`
- Socket handlers: `sockets/`
- Frontend:
  - templates: `templates/dashboard.html`, `templates/login.html`
  - scripts: `static/js/dashboard.js`
- Schema/bootstrap: `init.sql`

## Main Flows
1. User registers/logs in and receives an API key.
2. User opens dashboard and connects by Socket.IO.
3. User places order -> backend validates -> matching engine processes order.
4. Trades/positions/balances/order book are updated in DB.
5. Server emits realtime events to clients.
6. Admin can start game session with countdown and end event.

## Known Risk Areas
- Some mutating behavior still historically tied to GET-style usage in codebase context.
- API contracts and field naming can be inconsistent across backend/frontend.
- Realtime ordering and shared mutable state need careful handling.
- Missing or environment-specific files were previously observed in exploration (`config.py`-style dependency expectations).
- Test coverage is still limited for critical trading invariants.

## Technical Priorities (Agreed)
1. Use POST + JSON for mutating endpoints and avoid secrets in query strings.
2. Standardize error handling and HTTP status codes.
3. Stabilize backend/frontend response contracts.
4. Improve DB integrity with transaction-safe trade operations.
5. Expand automated tests (endpoint + matching engine + realtime scenarios).

## Cursor Project Guidance Added
The repository now includes:
- `AGENTS.md` with run/test/debug conventions.
- `.cursor/rules/`:
  - `python-backend-standards.mdc`
  - `api-security-and-http.mdc`
  - `realtime-socketio-safety.mdc`
  - `mysql-data-integrity.mdc`
  - `testing-and-regression-gates.mdc`
- `.cursor/skills/`:
  - `debug-async-race`
  - `websocket-test-harness`
  - `tdd-endpoint-flow`
  - `code-review-risk-first`
  - `security-audit-api-ws`
  - `incident-triage-realtime`
  - `perf-regression-guard`
  - `arch-decision-record`
  - `docs-runtime-ops`
  - `observability-backend`

## Recommended Resume Procedure
When context is lost:
1. Read this file (`context.md`) first.
2. Read `AGENTS.md` for command and workflow conventions.
3. Inspect `app.py`, `services/trade.py`, `models/order.py`, and `static/js/dashboard.js`.
4. Reconfirm active priority with user (security, feature, bugfix, or refactor).

## Useful Commands
- Setup:
  - `python -m venv .venv`
  - `.venv\Scripts\Activate.ps1`
  - `pip install -r requirements.txt`
- Run:
  - `python app.py`
  - `docker compose up --build`
- Validate:
  - `pytest -q`
  - `ruff check .` (if configured)
  - `mypy .` (if configured)

## Notes
- Keep this file concise and update it after major architecture or workflow changes.
- This file is a project memory aid, not a replacement for code-level documentation.
