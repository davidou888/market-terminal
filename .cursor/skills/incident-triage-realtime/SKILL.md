---
name: incident-triage-realtime
description: Triages realtime production incidents with a structured mitigation-first process. Use when users report downtime, missing events, lag, or inconsistent trading state.
---

# Incident Triage Realtime

## Goal
Restore service quickly and safely while preserving evidence.

## Workflow
1. Capture symptom timeline and affected scope.
2. Classify severity and immediate business impact.
3. Apply safe mitigation (feature flag, temporary fallback, rate limit).
4. Gather logs and event traces for root-cause analysis.
5. Propose permanent fix and regression test plan.
6. Produce concise postmortem action items.

## Output
- Incident summary
- Mitigation taken
- Root cause hypothesis
- Next actions with owners
