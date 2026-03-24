---
name: tdd-endpoint-flow
description: Applies test-driven development for HTTP endpoint changes, including success and failure paths. Use when adding or modifying Flask routes or request validation.
---

# TDD Endpoint Flow

## Goal
Ship endpoint changes with minimal regressions.

## Workflow
1. Write failing test for desired behavior.
2. Add failing test for one invalid input case.
3. Implement minimal route/service change.
4. Return explicit status codes and stable JSON shape.
5. Refactor without changing behavior.
6. Re-run relevant tests and summarize impact.

## Contract Rules
- Prefer JSON body for mutating operations.
- Keep response envelope predictable: `ok`, `data`, `error`.
