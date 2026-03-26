---
name: websocket-test-harness
description: Builds and runs repeatable websocket test scenarios for connect, disconnect, broadcast, and payload compatibility. Use when changing socket events or realtime flows.
---

# WebSocket Test Harness

## Goal
Validate realtime behavior before and after socket-related changes.

## Workflow
1. List events impacted by the change.
2. Define expected payload schema for each event.
3. Run multi-client scenario: connect, subscribe, emit, disconnect, reconnect.
4. Verify event ordering and payload fields.
5. Document any non-deterministic behavior and likely causes.
6. Add or update at least one automated test case when possible.

## Checklist
- Event names unchanged or migration documented
- Payload fields consistent with frontend consumers
- No silent failures on disconnect/reconnect
