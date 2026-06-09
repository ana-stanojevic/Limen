# Bounded Application Workflow

The Bounded Application Workflow is the first executable module inside Limen.

It evaluates whether a professional opportunity is worth pursuing based on a user profile, job description, explicit decision policy, and bounded agentic workflow design.

The focus is not application volume.

The focus is fit, clarity, quality, and human-controlled execution.

## Purpose

This module is designed to help users decide whether an opportunity should be:

- prepared
- queued
- skipped
- escalated for human review

## Current Milestone

**Milestone 1 — Bounded Application Workflow MVP** — completed.

The first executable evaluation engine is in place: input/output contract, job description parsing, profile matching, decision policy, runtime API, tests, and CI.

**Milestone 2 — Signal Extraction** — completed.

Structured signals are extracted from job descriptions and drive matching, decision risks, missing information, and escalation guardrails.

Focus:

- required skills
- preferred skills
- seniority signals
- production expectations
- ambiguity and risk indicators
- missing signals

**Milestone 3 — Agentic Workflow Layer** — in progress.

Introduce bounded agentic orchestration on top of the evaluation engine with explicit workflow states and human review gates.

Focus:

- separate planning from execution
- define agent responsibilities
- add explicit workflow states
- introduce human review points
- keep decisions observable and auditable

Later milestones introduce retrieval, tool use, agent memory, multi-agent collaboration, evaluation at scale, policy adaptation, and production platform capabilities.

See the full sequence in [`../../docs/ROADMAP.md`](../../docs/ROADMAP.md) (Milestones 4–12).

## System Boundary

This module does not submit applications automatically.

It supports decision-making and preparation while keeping final actions human-controlled.

## Run the API locally

From this module directory:

```bash
poetry install
poetry run uvicorn app.api.main:app --reload
```

Run tests:

```bash
poetry run pytest
```

## CI

GitHub Actions runs `poetry run pytest` on pushes and pull requests to `main` when this module changes.

Workflow: [`.github/workflows/bounded-application-workflow.yml`](../../.github/workflows/bounded-application-workflow.yml)

Python versions tested in CI: 3.11, 3.12, 3.13.

- `GET /health` — liveness check
- `POST /workflow/run` — evaluate a `WorkflowInput` and return `WorkflowOutput`

## Documentation

Core product and architecture documentation lives in the root documentation folder:

- [`../../docs/PRD.md`](../../docs/PRD.md)
- [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) — includes the plan → execution flow diagram for Milestone 3
- [`../../docs/ROADMAP.md`](../../docs/ROADMAP.md)

