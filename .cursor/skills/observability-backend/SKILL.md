---
name: observability-backend
description: Adds and reviews logs, metrics, and traces for backend and realtime flows. Use when diagnosing production issues or improving monitoring coverage.
---

# Observability Backend

## Goal
Improve visibility into request, trade, and socket event lifecycles.

## Workflow
1. Define key signals: latency, error rate, throughput, saturation.
2. Add structured logs with stable fields and correlation IDs.
3. Add metrics around critical operations and failures.
4. Ensure errors include context without exposing secrets.
5. Validate observability output with a local test scenario.

## Minimum Fields
- `event`
- `user_id` or anonymous marker
- `symbol` when trading-related
- `request_id` or correlation token
