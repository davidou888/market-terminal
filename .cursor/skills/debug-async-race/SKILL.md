---
name: debug-async-race
description: Diagnoses race conditions and async timing bugs in Flask-SocketIO and gevent flows. Use when behavior is intermittent, order-dependent, or appears only under concurrent clients.
---

# Debug Async Race

## Goal
Find and fix intermittent bugs caused by concurrent state changes.

## Workflow
1. Identify shared mutable state touched by multiple requests/events.
2. Reproduce with a deterministic sequence of parallel actions.
3. Add targeted logs around read-modify-write critical sections.
4. Confirm ordering assumptions and missing synchronization.
5. Implement minimal guard (lock, atomic section, or state refactor).
6. Add a regression test or repeatable script.

## Output Format
- Root cause
- Affected files
- Minimal safe fix
- Regression check command
