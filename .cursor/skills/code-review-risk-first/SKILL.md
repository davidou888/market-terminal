---
name: code-review-risk-first
description: Reviews code with a risk-first lens focused on correctness, regressions, security, and missing tests. Use when asked to review changes or assess production readiness.
---

# Code Review Risk First

## Goal
Prioritize issues that can break behavior or compromise security.

## Workflow
1. Identify high-risk surfaces first: auth, DB writes, realtime events.
2. Check for correctness and edge cases before style concerns.
3. Verify error handling and status code consistency.
4. Validate API and event schema compatibility.
5. Check whether tests cover changed behavior.
6. Return findings by severity with concrete file references.

## Severity
- Critical: must fix before merge
- High: likely regression/security issue
- Medium: correctness or maintainability risk
