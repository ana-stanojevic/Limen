# Agents

Each workflow stage is an agent behind a typed `Protocol` contract in [`contracts.py`](contracts.py). The orchestrator ([`orchestration/`](orchestration/)) drives them through the workflow state machine; [`wiring.py`](wiring.py) selects concrete implementations from the runtime config.

## Layout

Each stage agent is its own package under `app/agents/`:

```txt
signal_extraction/
  __init__.py        # Default* adapter (thin, deterministic)
  deterministic.py   # deterministic logic
  llm.py             # LLM-backed implementation (optional)
  prompts/           # versioned prompts (v1.txt, v2.txt, …) — marks it a runtime agent
```

The package directory name is the agent's registry name (`agent_name_for`), used to resolve its prompts and runtime config.

## Add a deterministic agent

1. Create `app/agents/{agent}/` with a logic module and a `Default{Agent}` adapter in `__init__.py` that implements the stage's `Protocol` from `contracts.py`.
2. Wire it into the orchestrator via `wiring.py`.

## Add an LLM-backed agent

1. Add `llm.py` with an `LLM{Agent}` that:
   - resolves its `AgentRuntimeConfig` via `config.agent_for(type(self))`;
   - calls the LLM inside an operation that raises typed errors;
   - runs through `BoundedAgentRuntime.execute` with a `PydanticOutputValidator`, a deterministic `fallback`, and a `RetryPolicy`;
   - attaches `result.without_output()` to its output's `execution` field for tracing.
2. Add versioned prompts under `prompts/{version}.txt`.
3. Add a runtime bundle in [`app/runtime/configs/`](../runtime/configs/) with `mode: llm` and a `prompt_version`.
4. Select deterministic vs. LLM wiring in `wiring.py` from the agent's `mode`.

`signal_extraction/llm.py` is the reference implementation; see the [runtime docs](../runtime/README.md) for the execution lifecycle.

## Current agents

| Agent | Stage | Modes |
|-------|-------|-------|
| `workflow_planning` | plan | deterministic |
| `signal_extraction` | extract signals | deterministic · llm |
| `profile_matching` | score alignment | deterministic |
| `decision_rules` | apply policy | deterministic |
| `human_review` | escalation gate | deterministic (passthrough) |
