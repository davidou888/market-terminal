---
name: perf-regression-guard
description: Detects and prevents performance regressions in critical request and websocket paths. Use when modifying matching logic, DB queries, or realtime broadcast loops.
---

# Perf Regression Guard

## Goal
Keep latency and throughput stable across code changes.

## Workflow
1. Define target path and baseline metric (`p95`, `p99`, throughput).
2. Run baseline measurement on current code.
3. Apply changes and rerun same scenario.
4. Compare metrics and identify regressions.
5. Optimize hot path if regression exceeds threshold.
6. Record benchmark command and threshold in notes.

## Default Threshold
- Flag if `p95` latency worsens by more than 15%.
