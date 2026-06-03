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

Milestone 1 focuses on building the first working evaluation engine.

Implementation scope:

1. input/output contract
2. job description parsing
3. profile matching
4. decision policy
5. runtime API
6. tests and CI

## System Boundary

This module does not submit applications automatically.

It supports decision-making and preparation while keeping final actions human-controlled.

## Documentation

Core product and architecture documentation lives in the root documentation folder:

- [`../../docs/PRD.md`](../../docs/PRD.md)
- [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`../../docs/ROADMAP.md`](../../docs/ROADMAP.md)

