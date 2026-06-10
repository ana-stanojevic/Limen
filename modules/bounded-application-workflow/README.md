# Bounded Application Workflow

First executable Limen module. Evaluates whether an opportunity is worth pursuing based on user profile, job description, and a bounded decision policy.

Decisions: `prepare` · `queue` · `skip` · `escalate` (human review). Does not submit applications or take autonomous actions.

**Phase:** Milestone 4 — LLM-Backed Agent Runtime (Milestones 1–3 complete). See [ROADMAP](../../docs/ROADMAP.md).

## Implemented

- Workflow state machine — explicit states and validated transitions (`WorkflowStateMachine`)
- Workflow run model — every run recorded and reconstructable (`WorkflowRun`)
- Planning layer — stages selected before execution, plan vs. execution compared (`WorkflowPlan`)
- Agent contracts — typed input/output Protocol per agent
- Orchestrator — state-managed execution of the agent pipeline
- Human review path — escalated decisions approved or revised (`HumanReviewRecord`)
- Audit trail — timestamped events and per-agent traces (`WorkflowEvent`, `AgentTrace`)

## Run locally

```bash
poetry install
poetry run uvicorn app.api.main:app --reload
poetry run pytest
```

## API

- `GET /health` — liveness
- `POST /workflow/run` — evaluate `WorkflowInput` → `WorkflowOutput`

## CI

GitHub Actions runs `poetry run pytest` on pushes/PRs to `main` when this module changes (Python 3.11–3.13).

Workflow: [`.github/workflows/bounded-application-workflow.yml`](../../.github/workflows/bounded-application-workflow.yml)

## Documentation

- [PRD](../../docs/PRD.md) · [ARCHITECTURE](../../docs/ARCHITECTURE.md) · [ROADMAP](../../docs/ROADMAP.md)
