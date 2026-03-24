# Agent Operating Guide

## Project Context
- Stack: Python, Flask, Flask-SocketIO, MySQL.
- Main entrypoint: `app.py`.
- Core business logic: `services/` and `models/order.py`.
- Frontend assets: `templates/`, `static/js/`, `static/css/`.

## Local Run Commands
- Create env: `python -m venv .venv`
- Activate (PowerShell): `.venv\Scripts\Activate.ps1`
- Install deps: `pip install -r requirements.txt`
- Run app: `python app.py`
- Docker run: `docker compose up --build`

## Validation Commands
- Run tests: `pytest -q`
- Run single test file: `pytest tests/test_db.py -q`
- Basic lint (if configured): `ruff check .`
- Type check (if configured): `mypy .`

## Coding Conventions
- Keep endpoint contracts stable and explicit.
- Prefer server-side validation for all external input.
- Avoid GET for state-changing operations.
- Use parameterized SQL and never build SQL with string interpolation.
- Keep business rules in services/models, not in route handlers.

## Realtime Safety
- Treat WebSocket events as untrusted input.
- Keep event payload schemas consistent and version-safe.
- Minimize shared mutable state and protect critical sections.

## Change Workflow
1. Reproduce issue or define acceptance criteria.
2. Implement minimal safe change.
3. Add/adjust tests near changed behavior.
4. Run validation commands.
5. Summarize risk and follow-up tasks.

## Review Focus
- Correctness of matching and position updates.
- Error handling and HTTP status codes.
- API schema consistency between backend and `static/js/dashboard.js`.
- Security basics: auth checks, secrets handling, and input validation.
