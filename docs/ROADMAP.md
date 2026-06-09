# Roadmap

## Milestone 1 — Bounded Application Workflow MVP — completed

Goal: build the first executable workflow inside Limen.

The module evaluates opportunities against a user profile and decides whether the system should:

- prepare
- queue
- skip
- escalate

Implementation focus:

1. input/output contract
2. job description parsing
3. profile matching
4. decision policy
5. runtime API
6. tests and CI

Done when:

- the module can be run locally
- an opportunity can be evaluated through an API endpoint
- the decision policy is covered by tests
- CI validates the implementation

## Milestone 2 — Signal Extraction — completed

Improve structured extraction from job descriptions and user profiles.

Focus:

- required skills
- preferred skills
- seniority signals
- production expectations
- ambiguity and risk indicators
- missing signals

Done when:

- job descriptions yield structured signal categories
- user profiles expose seniority and production experience fields
- matcher incorporates signal-level alignment and risk detection
- extraction and matching are covered by tests and fixtures

## Milestone 3 — Agentic Workflow Layer — in progress

Introduce bounded agentic orchestration.

Focus:

- separate planning from execution
- define agent responsibilities
- add explicit workflow states
- introduce human review points
- keep decisions observable and auditable

Done when:

- workflow states are explicit and transition through a defined state machine
- planning and execution are separate stages with clear boundaries
- each agent has a defined responsibility and input/output contract
- human review points are wired into escalation paths
- state transitions and decisions are logged and inspectable

## Milestone 4 — LLM-Backed Agent Runtime

Introduce LLM-backed implementations for selected workflow agents while preserving typed contracts, deterministic fallbacks, and auditable execution.

Focus:

- LLM structured output for job signal extraction
- prompt/versioned agent configurations
- tool-ready agent interface
- model fallback and retry policy
- validation of LLM outputs against Pydantic schemas
- evaluation set for extraction and decision quality
- tracing of prompts, outputs, errors, and decisions

Done when:

- at least one workflow agent has an LLM-backed implementation behind the existing Protocol contract
- LLM outputs are validated against Pydantic schemas before entering the workflow
- deterministic fallback is used when the model fails or output is invalid
- agent prompts and model configs are versioned and selectable at runtime
- extraction and decision quality can be measured against a fixed evaluation set
- prompts, outputs, errors, and final decisions are traced for inspection

## Milestone 5 — User-Facing Demo

Expose the workflow through a simple interface.

Focus:

- paste job description
- evaluate opportunity
- show score, decision, missing signals, risks, and reasoning summary

## Milestone 6 — Early Reliability Baseline

Establish the minimum observability and validation needed before LLM-backed agents and tool use go into production.

Focus:

- schema validation for all agent outputs
- basic execution tracing and workflow event logging
- prompt version tracking
- initial benchmark fixtures

Done when:

- all agent outputs pass Pydantic validation before entering the workflow
- workflow runs are inspectable through `WorkflowRun` events
- prompt and model configs are versioned
- a starter benchmark set exists for regression checks

The full evaluation program continues in Milestone 9.

## Milestone 7 — Retrieval & Tooling Layer

Introduce tool-use and retrieval as first-class workflow capabilities.

Focus:

- tool registry
- tool contracts
- retriever abstraction
- vector search
- knowledge sources
- tool selection policies
- structured tool invocation

Done when:

- agents can invoke tools through typed contracts
- tool calls are typed and schema-validated
- retrieval is separated from agent logic
- tool outputs are validated before use
- tool execution is auditable

## Milestone 8 — Agent Memory & Context Management

Give agents controlled access to prior step results and durable context.

This is the point where the system starts to behave like a serious agent platform rather than a single-pass pipeline.

Focus:

- short-term memory
- artifacts
- context windows
- working memory
- memory persistence
- memory pruning

Done when:

- agents can use results from previous workflow steps
- context size and scope are explicitly controlled
- memory can be reconstructed from `WorkflowRun`

## Milestone 9 — Evaluation & Reliability

Build a dedicated evaluation layer so quality, regressions, and failures are measurable engineering concerns — not ad-hoc manual checks.

Focus:

- golden datasets
- agent evals
- workflow evals
- regression tests
- confidence scoring
- fallback policies
- failure analysis
- cost tracking

Done when:

- every change can be measured against benchmarks
- quality has explicit metrics
- prompts have a regression suite
- agent failures are classified and actionable

## Milestone 10 — Multi-Agent Collaboration

Multiple specialized agents collaborate under orchestrator control.

This is what people usually imagine when they say "agent system."

Focus:

- planner agent
- executor agent
- critic agent
- review agent
- agent handoffs
- shared artifacts

Done when:

- multiple agents collaborate on a single workflow run
- agent responsibilities are isolated behind contracts
- the orchestrator manages handoffs and shared state

## Milestone 11 — Learning & Policy Adaptation

Close the loop between outcomes and future decisions.

This corresponds to the feedback and adaptation layer in the system architecture.

Focus:

- outcome tracking
- policy tuning
- threshold adaptation
- feedback loops
- decision calibration

Done when:

- outcomes influence future decisions
- ranking changes through feedback
- escalation policy adapts based on observed results

## Milestone 12 — Production AI Platform

Operate the workflow as a production-grade AI platform with full observability, reproducibility, and experimentation support.

Focus:

- observability dashboards
- cost monitoring
- latency monitoring
- trace explorer
- run replay
- versioned workflows
- versioned prompts
- A/B testing

Done when:

- any workflow run can be reproduced
- every decision can be explained from trace data
- any run can be replayed
- model or prompt changes can be compared through controlled experiments

