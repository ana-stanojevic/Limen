# PRD — Bounded Application Workflow

## Overview

The Bounded Application Workflow module evaluates whether a professional opportunity is worth pursuing based on structured signals from a user's background and a job description.

The goal of the module is not to automate applications at scale, but to support deliberate, high-quality career decisions through bounded evaluation and human review.

This module represents the first executable component of the broader Limen platform.

**Current phase:** Milestone 3 — Agentic Workflow Layer. Milestones 1 (MVP) and 2 (Signal Extraction) are complete. The module now moves from a single-pass evaluation pipeline to bounded agentic orchestration with explicit workflow states, agent responsibilities, and human review points.

---

# Problem

Modern job searching is noisy, fragmented, and cognitively expensive.

Most existing systems optimize for:

- application volume,
- automation speed,
- engagement metrics,
- keyword matching.

They rarely help users answer more important questions:

- Is this opportunity actually aligned with my background?
- What signals are missing?
- Is this role realistically attainable?
- Is it worth investing time and emotional energy into?
- Should this opportunity be pursued now, later, or not at all?

The result is decision fatigue, low-quality applications, and poor alignment between people and opportunities.

---

# Target User

Initial target users:

- technical professionals,
- researchers transitioning into industry,
- multidisciplinary candidates with non-linear careers.

The system is designed for users who value:

- quality over quantity,
- strategic applications,
- deliberate career navigation,
- bounded automation.

---

# Core Evaluation Engine (Milestones 1 & 2 — completed)

The module ships a working evaluation engine that:

1. accepts a user profile and job description,
2. extracts structured opportunity signals,
3. scores profile alignment,
4. applies a bounded decision policy,
5. returns a structured recommendation via API.

The module **evaluates** opportunities — it helps decide prepare, queue, skip, or escalate. It does **not** apply to jobs, send emails, automate browsers, or take autonomous actions on the user's behalf.

---

# Milestone 3 Scope — Agentic Workflow Layer (current)

## Goal

Evolve the evaluation engine into a bounded agentic workflow where decisions are orchestrated through explicit states, specialized agents, and human oversight.

## Agent Responsibilities

| Agent | Responsibility |
| ----- | -------------- |
| Workflow Planner | Plan evaluation scope, required signals, guardrails, and workflow stages before execution |
| Signal Extractor | Parse job descriptions into structured signal categories |
| Profile Matcher | Score profile alignment against extracted signals |
| Decision Policy | Apply bounded thresholds and escalation rules |
| Workflow Orchestrator | Manage state transitions and coordinate agent stages |
| Human Review Gate | Pause execution for ambiguous or high-stakes decisions |

## Workflow States

The workflow progresses through explicit states rather than a single request-response cycle:

```
intake → signal_extraction → profile_matching → policy_evaluation → [human_review] → decision
```

Escalation paths route ambiguous evaluations to human review before a final decision is emitted.

## Requirements

- planning and execution are separate stages with clear boundaries
- each agent has a defined input/output contract
- workflow state is explicit and persisted across stages
- human review points are wired into escalation paths
- state transitions and agent outputs are logged and inspectable

## Non-Goals (Milestone 3)

- unconstrained multi-agent autonomy
- LLM-driven decision overrides without policy bounds

---

# Inputs

## User Profile

Structured or semi-structured profile information.

Example fields:

- experience summary,
- technical skills,
- research background,
- production experience,
- preferred domains,
- location constraints,
- seniority indicators.

## Job Description

Raw job posting text.

The system extracts:

- required skills,
- preferred skills,
- domain alignment,
- seniority expectations,
- execution signals,
- production requirements,
- ambiguity or risk indicators.

---

# Outputs

The module returns a structured evaluation object.

Example:

```
{
  "score": 0.82,
  "decision": "prepare",
  "missing_signals": ["large-scale production inference"],
  "risks": ["high infrastructure ownership expectations"],
  "reasoning_summary": "Strong AI systems alignment with partial production gaps."
}
```

---

# Decision Categories

## prepare

High alignment. Recommended for active pursuit.

## queue

Potential fit, but not currently a priority.

## escalate

Requires human review due to ambiguity or conflicting signals.

## skip

Low alignment or poor strategic fit.

---

# Decision Policy

Current score thresholds:


| Score Range | Decision |
| ----------- | -------- |
| >= 0.75     | prepare  |
| >= 0.55     | queue    |
| >= 0.35     | escalate |
| < 0.35      | skip     |


The policy is intentionally simple and deterministic. Guardrails (for example, risk-based escalation) are applied through the workflow plan and decision rules.

Future versions incorporate:

- confidence estimation,
- uncertainty handling,
- weighted signals,
- user-specific preferences,
- memory systems.

---

# What the module does not do

The module does not:

- apply to jobs or submit applications,
- send emails,
- automate browser workflows,
- optimize resumes,
- perform autonomous actions,
- replace human judgment,
- maximize application count,
- scrape job platforms at scale,
- simulate a general autonomous agent.

---

# Technical Scope (implemented)

Current implementation includes:

- Python backend,
- FastAPI service,
- deterministic decision policy and signal extraction,
- bounded agentic orchestration with explicit workflow states,
- modular domain layer,
- test coverage,
- CI pipeline,
- example inputs and outputs.

LLM-backed agents are planned for Milestone 4. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the plan → execution flow.

---

# Success Criteria

## Milestones 1 & 2 — delivered

The core evaluation engine described above is implemented and shipped.

## Milestone 3 (current)

- workflow progresses through explicit, logged states,
- planning and execution are separated with clear agent boundaries,
- escalation routes to human review before final decision,
- state transitions and agent outputs are inspectable,
- serves as a foundation for the user-facing demo (Milestone 4).

---

# Open Questions

- How should uncertainty be represented?
- How should user preferences influence scoring?
- Which signals deserve the highest weighting?
- What level of explainability should future versions expose?
- Should future policies become adaptive or remain bounded?

---

