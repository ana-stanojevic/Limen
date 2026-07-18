# Roadmap

## Milestone 1 — MVP — completed

Executable evaluation workflow: I/O contract, job parsing, profile matching, decision policy, API, tests, CI.

## Milestone 2 — Signal Extraction — completed

Structured signals from job descriptions and profiles: skills, seniority, production expectations, ambiguity/risk, missing signals. Matcher and extractor covered by tests.

## Milestone 3 — Agentic Workflow Layer — completed

Bounded agentic orchestration: planning/execution separation, agent contracts, explicit workflow states, human review on escalation, auditable transitions.

**Done when:** state machine is explicit; each agent has I/O contract; escalation routes to human review; transitions and outputs are logged and inspectable.

## Milestone 4 — LLM-Backed Agent Runtime — completed

LLM implementations behind existing Protocol contracts with typed fallbacks and auditable execution.

**Focus:** structured extraction · versioned prompts/configs · tool-ready interface · fallback/retry · Pydantic validation · eval set · tracing.

**Done when:** ≥1 LLM-backed agent with schema validation, deterministic fallback, versioned configs, eval set, and full traceability.

## Milestone 5 — Framework Migration

Adopt the 2026 agent stack behind the existing contracts and decision policy, replacing the hand-built primitives from M1–M4. See [ADR 0001](adr/0001-adopt-modern-agent-stack.md).

**Focus:** Pydantic AI (agents) · LangGraph (orchestration/state + human-in-the-loop) · Pydantic Logfire (observability) · Pydantic Evals (evaluation) · dependency/tooling modernization.

**Done when:** agents run on Pydantic AI with typed outputs and deterministic fallback; orchestration and state run on LangGraph with escalation via interrupts; runs are traced in Logfire; evaluation runs on Pydantic Evals; dependencies are current; output parity with the pre-migration workflow is preserved.

## Milestone 6 — User-Facing Demo

Paste job description → evaluate → show score, decision, missing signals, risks, reasoning. Built on the migrated stack — Next.js + CopilotKit streaming the LangGraph agent state into the UI.

## Milestone 7 — Early Reliability Baseline

Schema validation, execution tracing, prompt versioning, benchmark fixtures — built on Logfire traces and Pydantic Evals. Continues in Milestone 10.

**Done when:** all outputs Pydantic-validated; runs inspectable via Logfire/LangGraph checkpoints; versioned configs; starter benchmark set.

## Milestone 8 — Retrieval & Tooling

Tool registry, contracts, retriever abstraction, vector search, tool selection, schema-validated invocation via Pydantic AI tools / MCP.

## Milestone 9 — Agent Memory & Context

Short-term/working memory, artifacts, context windows, persistence, pruning — via LangGraph checkpointers and state reducers, backed by PostgreSQL + `pgvector`.

## Milestone 10 — Evaluation & Reliability

Golden datasets, agent/workflow evals, regression tests, confidence scoring, fallback policies, failure analysis, cost tracking — on Pydantic Evals + Logfire.

**Done when:** changes measured against benchmarks; prompts have regression suite; failures classified and actionable.

## Milestone 11 — Multi-Agent Collaboration

Planner, executor, critic, review agents under orchestrator control with handoffs and shared artifacts — as LangGraph subgraphs.

## Milestone 12 — Learning & Policy Adaptation

Outcome tracking, threshold adaptation, feedback loops, decision calibration.

## Milestone 13 — Production AI Platform

Observability dashboards, cost/latency monitoring, trace explorer, run replay, versioned workflows/prompts, A/B testing — on Logfire.

**Done when:** any run reproducible, explainable from trace data, and comparable across model/prompt experiments.
