## Agentic

The architecture of the Bounded Application Workflow module is agent-oriented.

Instead of relying on a single monolithic LLM interaction, the system is designed around specialized bounded agents responsible for:

- opportunity understanding,
- signal extraction,
- profile interpretation,
- decision support,
- workflow orchestration,
- human escalation,
- execution safety.

<br>
<p align="center">
  <img src="./images/runtime.png" width="500">
</p>

The system prioritizes:

- bounded execution,
- modular reasoning,
- explicit state transitions,
- tool-based workflows,
- observable decision chains,
- controllable autonomy.

Agentic behavior is introduced incrementally and remains constrained by explicit policies and human oversight.

---

# Current Phase — Milestone 3: Agentic Workflow Layer

Milestones 1 and 2 delivered a working evaluation engine with structured signal extraction. Milestone 3 introduces bounded agentic orchestration on top of that foundation.

## Workflow State Machine

```
intake
  → signal_extraction
  → profile_matching
  → policy_evaluation
  → [human_review]
  → decision
```

Each state has a defined entry condition, responsible agent, and output contract. Transitions are explicit and logged.

## Agent Boundaries

| Stage | Agent | Input | Output |
| ----- | ----- | ----- | ------ |
| planning | Workflow Planner | `WorkflowInput` | `WorkflowPlan` |
| signal_extraction | Signal Extractor | job description + `plan.required_signals` | `JobSignals` |
| profile_matching | Profile Matcher | `JobSignals` + `UserProfile` + `plan.required_signals` | `ProfileMatchResult` |
| policy_evaluation | Decision Policy | `ProfileMatchResult` + `JobSignals` + `WorkflowPlan` | `WorkflowDecision` |
| human_review | Human Review Gate | escalated `WorkflowDecision` + `EvaluationBrief` | approved or revised decision |
| orchestration | Workflow Orchestrator | workflow input | state-managed `WorkflowOutput` |

Planning (what to evaluate, which signals matter, which guardrails apply) is separated from execution (running agents, applying policy, emitting decisions). The plan is the single source of truth for evaluation scope and policy guardrails; downstream stages read from it rather than re-deriving the same heuristics.

## Plan → Execution Flow

The planner runs once before the stage loop. Every downstream stage consumes fields from `WorkflowPlan`:

- `required_signals` — which signal categories to extract, score, and highlight
- `evaluation_focus` — what the evaluation brief emphasizes
- `requires_risk_guardrail` — whether a strong match should be downgraded to escalate
- `requires_human_review` — whether the pipeline includes a human review checkpoint
- `stages` — ordered workflow states the orchestrator executes

```mermaid
flowchart TD
    P[Planner: build_workflow_plan] --> Plan[WorkflowPlan]
    Plan --> E[Signal Extraction]
    Plan --> M[Profile Matching]
    Plan --> D[Decision Policy]
    Plan --> H[Human Review Gate]
    Plan --> B[Evaluation Brief]

    E -->|"required_signals"| M
    M --> D
    D -->|"requires_risk_guardrail"| H
```

The human review gate runs only when the plan reserved that stage **and** the policy produced an `ESCALATE` decision. The final decision always comes from policy evaluation at runtime; the plan configures *how* to evaluate, not *what* the match score will be.

## Milestone 3 Deliverables

- explicit workflow state machine
- agent responsibility contracts
- planning/execution separation
- human review integration on escalation paths
- observable state transitions and decision chains

## Later Milestones (4–12)

| Milestone | Theme |
| --------- | ----- |
| 4 | LLM-backed agent runtime |
| 5 | User-facing demo |
| 6 | Early reliability baseline |
| 7 | Retrieval & tooling layer |
| 8 | Agent memory & context management |
| 9 | Evaluation & reliability |
| 10 | Multi-agent collaboration |
| 11 | Learning & policy adaptation |
| 12 | Production AI platform |

Full definitions: [`ROADMAP.md`](./ROADMAP.md).

---

# Future Iterations

Later milestones introduce:

- LLM-backed agents with typed fallbacks (Milestone 4),
- retrieval and tool-use layers (Milestone 7),
- agent memory and context management (Milestone 8),
- evaluation and reliability at scale (Milestone 9),
- multi-agent collaboration (Milestone 10),
- learning and policy adaptation (Milestone 11),
- production platform observability and replay (Milestone 12).

The system is intentionally designed to evolve toward production-grade agentic workflows rather than simple prompt-response interactions.

---

# Architectural Principles

## Bounded Autonomy

Agents operate within explicit constraints and policy boundaries.

## Human Oversight

High-ambiguity decisions require escalation or review.

## Observable Reasoning

System decisions should remain inspectable and debuggable.

## Modular Agents

Capabilities should be isolated into composable components instead of hidden inside a single prompt.

## Production Orientation

The architecture prioritizes reliability, evaluation, monitoring, and controlled execution over unconstrained autonomy.




