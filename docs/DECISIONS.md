# Decisions

## ADR-001 — Start with a bounded workflow before autonomous execution

Status: Accepted

Limen starts with the Bounded Application Workflow as the first executable module.

The initial implementation focuses on:

- explicit input and output contracts
- opportunity evaluation
- profile matching
- deterministic decision policy
- human-controlled execution

This keeps the system reviewable, testable, and safe before introducing more advanced agentic orchestration.

## ADR-002 — Keep module actions human-controlled in the MVP

Status: Accepted

The MVP does not automatically submit applications.

The system may evaluate, prepare, queue, skip, or escalate an opportunity, but final submission remains under human control.

This prevents premature automation and keeps the workflow aligned with quality-first application decisions.