# PRD — Bounded Application Workflow

## Overview

Evaluates whether a professional opportunity is worth pursuing from structured signals in a user profile and job description.

Supports deliberate, high-quality career decisions — not application volume or autonomous actions. First executable Skaut Careers module.

**Phase:** Milestones 1–4 complete — LLM-Backed Agent Runtime delivered. See [ARCHITECTURE.md](./ARCHITECTURE.md) for workflow states and agent boundaries.

---

## Problem

Job search is noisy and cognitively expensive. Existing tools optimize volume, speed, and keyword matching — not whether an opportunity is aligned, attainable, or worth the investment.

**Target users:** technical professionals, researchers entering industry, multidisciplinary candidates with non-linear careers. Users who value quality, strategic applications, and bounded automation.

---

## Core Engine (Milestones 1–2 — delivered)

1. Accept user profile + job description
2. Extract structured opportunity signals
3. Score profile alignment
4. Apply bounded decision policy
5. Return structured recommendation via API

The module **evaluates** (prepare, queue, skip, escalate). It does **not** apply to jobs, send emails, automate browsers, optimize resumes, or scrape platforms at scale.

---

## Milestone 3 — Agentic Workflow Layer (delivered)

Evolved the engine into bounded agentic orchestration with explicit states, specialized agents, and human oversight.

**Requirements (all met):**

- planning and execution are separate stages
- each agent has a defined input/output contract
- workflow state is explicit and persisted
- escalation routes to human review before final decision
- state transitions and agent outputs are logged and inspectable

**Non-goals:** unconstrained multi-agent autonomy; LLM overrides without policy bounds.

---

## Milestone 4 — LLM-Backed Agent Runtime (delivered)

Added a shared runtime so agents can be LLM-backed behind the same contracts, without changing the orchestrator or state machine.

**Requirements (all met):**

- at least one LLM-backed agent behind an existing `Protocol` contract
- schema-validated outputs with deterministic fallback on failure
- bounded, retryable execution with contained errors
- versioned prompts and runtime configs, selected per run
- execution tracing and an evaluation dataset for measurable quality

**Non-goals:** autonomous actions; unbounded retries; LLM output accepted without validation or fallback.

---

## Inputs

**User profile** — experience, skills, research/production background, domains, location, seniority.

**Job description** — raw posting text. System extracts required/preferred skills, domain alignment, seniority, execution signals, production requirements, ambiguity/risk indicators.

---

## Outputs

Structured evaluation object:

```json
{
  "score": 0.82,
  "decision": "prepare",
  "missing_signals": ["large-scale production inference"],
  "risks": ["high infrastructure ownership expectations"],
  "reasoning_summary": "Strong AI systems alignment with partial production gaps."
}
```

### Decision categories

| Decision | Meaning |
| -------- | ------- |
| prepare | High alignment — pursue actively |
| queue | Potential fit, not current priority |
| escalate | Ambiguity or conflicting signals — human review |
| skip | Low alignment or poor strategic fit |

### Policy thresholds

| Score | Decision |
| ----- | -------- |
| ≥ 0.75 | prepare |
| ≥ 0.55 | queue |
| ≥ 0.35 | escalate |
| < 0.35 | skip |

Deterministic and simple. Risk-based escalation via workflow plan and decision rules. Future: confidence, uncertainty, weighted signals, user preferences, memory.

---

## Technical Scope

Python · FastAPI · deterministic and LLM-backed agents behind typed contracts · bounded agentic orchestration · runtime validation/fallback · versioned prompts and configs · modular domain layer · tests · CI.

Implementation details: [module README](../modules/bounded-application-workflow/README.md).

---

## Success Criteria

**Milestones 1–2:** core evaluation engine shipped.

**Milestone 3:** delivered — explicit logged states · planning/execution separation · human review on escalation · inspectable transitions · foundation for user-facing demo (Milestone 5).

**Milestone 4:** delivered — ≥1 LLM-backed agent behind existing contracts · schema validation · deterministic fallback · versioned prompts/configs · execution tracing · evaluation dataset.

---

## Open Questions

- How should uncertainty and user preferences influence scoring?
- Which signals deserve highest weighting?
- What explainability should future versions expose?
- Should policies remain bounded or become adaptive?
