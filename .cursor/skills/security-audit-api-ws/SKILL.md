---
name: security-audit-api-ws
description: Performs focused security audits for Flask HTTP and Socket.IO event surfaces using practical OWASP-style checks. Use when changing auth, endpoints, API keys, or websocket handlers.
---

# Security Audit API WS

## Goal
Reduce exploit risk in API and realtime boundaries.

## Workflow
1. Map trust boundaries and sensitive operations.
2. Verify authn/authz checks happen before state changes.
3. Ensure no secrets are leaked in query strings or logs.
4. Check input validation, rate-limit exposure, and error leakage.
5. Validate SQL safety and dependency risk where relevant.
6. Provide prioritized remediation list with effort estimates.

## Quick Checks
- No mutating `GET` endpoints
- No API key in URL
- Clear forbidden vs unauthorized responses
