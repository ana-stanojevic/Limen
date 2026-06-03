# Roadmap

## Milestone 1 — Bounded Application Workflow MVP

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

## Milestone 2 — Signal Extraction

Improve structured extraction from job descriptions and user profiles.

Focus:

- required skills
- preferred skills
- seniority signals
- production expectations
- ambiguity and risk indicators
- missing signals

## Milestone 3 — Agentic Workflow Layer

Introduce bounded agentic orchestration.

Focus:

- separate planning from execution
- define agent responsibilities
- add explicit workflow states
- introduce human review points
- keep decisions observable and auditable

## Milestone 4 — User-Facing Demo

Expose the workflow through a simple interface.

Focus:

- paste job description
- evaluate opportunity
- show score, decision, missing signals, risks, and reasoning summary