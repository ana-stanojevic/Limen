from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.contracts import (
    DecisionPolicy,
    DecisionPolicyInput,
    HumanReviewGate,
    HumanReviewGateInput,
    ProfileMatcher,
    ProfileMatcherInput,
    SignalExtractor,
    SignalExtractorInput,
)
from app.agents.decision_rules.rules import review_reason
from app.agents.orchestration.audit import (
    AgentTrace,
    HumanReviewRecord,
    WorkflowEvent,
    WorkflowEventType,
)
from app.agents.orchestration.state import WorkflowGraphState
from app.domain.job_signals import JobSignals
from app.domain.models import (
    DecisionType,
    JobDescription,
    ProfileMatchResult,
    UserProfile,
    WorkflowDecision,
    WorkflowInput,
    WorkflowOutput,
)
from app.agents.workflow_planning.plan import (
    DECISION,
    HUMAN_REVIEW,
    INTAKE,
    POLICY_EVALUATION,
    PROFILE_MATCHING,
    SIGNAL_EXTRACTION,
    PlanExecutionReport,
    WorkflowPlan,
    compare_plan,
)
from app.runtime.result import AgentExecutionResult, ExecutionStatus

_NEXT_STEPS: dict[DecisionType, list[str]] = {
    DecisionType.PREPARE: [
        "Tailor your CV to highlight matched skills and role alignment.",
        "Draft a concise cover letter addressing any remaining gaps.",
        "Prepare talking points for interviews based on the job description.",
    ],
    DecisionType.QUEUE: [
        "Save this opportunity for a later review cycle.",
        "Note what would need to change before actively pursuing it.",
        "Re-run evaluation if your profile or priorities shift.",
    ],
    DecisionType.ESCALATE: [
        "Review the opportunity manually before investing application time.",
        "Clarify ambiguous requirements with the recruiter or hiring team.",
        "Fill in missing profile or job signals, then re-evaluate.",
    ],
    DecisionType.SKIP: [
        "Record why this opportunity is not a fit for future reference.",
        "Focus search effort on roles that align with your target profile.",
    ],
}

_CHECKPOINT_TYPES = (
    UserProfile,
    JobDescription,
    WorkflowInput,
    WorkflowOutput,
    WorkflowDecision,
    ProfileMatchResult,
    DecisionType,
    JobSignals,
    WorkflowPlan,
    WorkflowEvent,
    WorkflowEventType,
    AgentTrace,
    HumanReviewRecord,
    PlanExecutionReport,
    AgentExecutionResult,
    ExecutionStatus,
)


def default_checkpointer() -> MemorySaver:
    """In-memory checkpointer with an allowlist for workflow domain types."""
    return MemorySaver(
        serde=JsonPlusSerializer(allowed_msgpack_modules=_CHECKPOINT_TYPES)
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _input_summary(state: WorkflowGraphState) -> str:
    company = state.job_description.company or "an unspecified company"
    return (
        f"{state.user_profile.name} is being evaluated for "
        f"{state.job_description.title} at {company}."
    )


def _event(
    event_type: WorkflowEventType,
    stage: str,
    message: str = "",
    *,
    timestamp: datetime | None = None,
) -> WorkflowEvent:
    return WorkflowEvent(
        event_type=event_type,
        stage=stage,
        timestamp=timestamp or _now(),
        message=message,
    )


def _enter_stage(
    events: list[WorkflowEvent],
    stage: str,
    message: str = "",
) -> list[WorkflowEvent]:
    return [*events, _event(WorkflowEventType.STAGE_ENTERED, stage, message)]


def _record_agent(
    traces: list[AgentTrace],
    events: list[WorkflowEvent],
    *,
    stage: str,
    agent: str,
    output: Any,
) -> tuple[list[AgentTrace], list[WorkflowEvent]]:
    timestamp = _now()
    traces = [
        *traces,
        AgentTrace(
            stage=stage,
            agent=agent,
            output=output.model_dump(),
            timestamp=timestamp,
        ),
    ]
    events = [
        *events,
        _event(
            WorkflowEventType.AGENT_COMPLETED,
            stage,
            f"Agent '{agent}' completed.",
            timestamp=timestamp,
        ),
    ]
    return traces, events


def build_workflow_graph(
    *,
    extractor: SignalExtractor,
    matcher: ProfileMatcher,
    policy: DecisionPolicy,
    review_gate: HumanReviewGate | None,
) -> StateGraph:

    def intake(state: WorkflowGraphState) -> dict[str, Any]:
        planned = " -> ".join(state.plan.stages)
        return {
            "events": [
                *state.events,
                _event(WorkflowEventType.RUN_STARTED, INTAKE, "Workflow run started."),
                _event(
                    WorkflowEventType.PLAN_CREATED,
                    INTAKE,
                    f"Planner selected stages: {planned}.",
                ),
            ]
        }

    def signal_extraction(state: WorkflowGraphState) -> dict[str, Any]:
        events = _enter_stage(state.events, SIGNAL_EXTRACTION)
        output = extractor.run(
            SignalExtractorInput(job_description=state.job_description)
        )
        traces, events = _record_agent(
            state.traces,
            events,
            stage=SIGNAL_EXTRACTION,
            agent=type(extractor).__name__,
            output=output,
        )
        return {
            "signals": output.signals,
            "events": events,
            "traces": traces,
        }

    def profile_matching(state: WorkflowGraphState) -> dict[str, Any]:
        if state.signals is None:
            raise RuntimeError("profile_matching requires signals on graph state")
        events = _enter_stage(state.events, PROFILE_MATCHING)
        output = matcher.run(
            ProfileMatcherInput(
                user_profile=state.user_profile,
                job_description=state.job_description,
                signals=state.signals,
            )
        )
        traces, events = _record_agent(
            state.traces,
            events,
            stage=PROFILE_MATCHING,
            agent=type(matcher).__name__,
            output=output,
        )
        return {
            "match": output.match,
            "events": events,
            "traces": traces,
        }

    def policy_evaluation(state: WorkflowGraphState) -> dict[str, Any]:
        if state.signals is None or state.match is None:
            raise RuntimeError("policy_evaluation requires signals and match")
        events = _enter_stage(state.events, POLICY_EVALUATION)
        output = policy.run(
            DecisionPolicyInput(match=state.match, signals=state.signals)
        )
        traces, events = _record_agent(
            state.traces,
            events,
            stage=POLICY_EVALUATION,
            agent=type(policy).__name__,
            output=output,
        )
        return {
            "decision": output.decision,
            "events": events,
            "traces": traces,
        }

    def decision(state: WorkflowGraphState) -> dict[str, Any]:
        if state.decision is None or state.signals is None or state.match is None:
            raise RuntimeError("decision requires decision, signals, and match")

        current = state.decision
        events = list(state.events)
        traces = list(state.traces)
        review = state.review

        # Escalate -> review stays here for now (issue 79 → LangGraph interrupt).
        if current.decision == DecisionType.ESCALATE:
            reason = review_reason(current)
            events = _enter_stage(events, HUMAN_REVIEW, reason)
            if review is not None:
                raise RuntimeError("A review was already recorded for this run")
            review = HumanReviewRecord(
                reason=reason,
                original_decision=current,
                requested_at=_now(),
            )
            events.append(
                _event(WorkflowEventType.REVIEW_REQUESTED, HUMAN_REVIEW, reason)
            )
            if review_gate is not None:
                gate_output = review_gate.run(
                    HumanReviewGateInput(
                        decision=current,
                        match=state.match,
                        signals=state.signals,
                        reason=reason,
                    )
                )
                traces, events = _record_agent(
                    traces,
                    events,
                    stage=HUMAN_REVIEW,
                    agent=type(review_gate).__name__,
                    output=gate_output,
                )
                review = review.model_copy(
                    update={
                        "final_decision": gate_output.decision,
                        "approved": gate_output.approved,
                        "reviewer_notes": gate_output.reviewer_notes,
                        "reviewed_at": _now(),
                    }
                )
                outcome = (
                    "approved"
                    if not review.is_revised
                    else f"revised to '{gate_output.decision.decision.value}'"
                )
                events.append(
                    _event(
                        WorkflowEventType.REVIEW_COMPLETED,
                        HUMAN_REVIEW,
                        f"Human review {outcome}.",
                    )
                )
                current = review.final_decision or current

        events = _enter_stage(events, DECISION)
        output = WorkflowOutput(
            input_summary=_input_summary(state),
            decision=current,
            job_signals=state.signals,
            recommended_next_steps=list(_NEXT_STEPS[current.decision]),
        )
        completed_at = _now()
        executed = [
            INTAKE,
            *[
                event.stage
                for event in events
                if event.event_type == WorkflowEventType.STAGE_ENTERED
            ],
        ]
        plan_report = compare_plan(state.plan, executed)
        events.append(
            _event(WorkflowEventType.RUN_COMPLETED, DECISION, "Workflow run completed.")
        )
        return {
            "decision": current,
            "output": output,
            "review": review,
            "events": events,
            "traces": traces,
            "completed_at": completed_at,
            "plan_report": plan_report,
        }

    graph = StateGraph(WorkflowGraphState)
    graph.add_node(INTAKE, intake)
    graph.add_node(SIGNAL_EXTRACTION, signal_extraction)
    graph.add_node(PROFILE_MATCHING, profile_matching)
    graph.add_node(POLICY_EVALUATION, policy_evaluation)
    graph.add_node(DECISION, decision)

    graph.add_edge(START, INTAKE)
    graph.add_edge(INTAKE, SIGNAL_EXTRACTION)
    graph.add_edge(SIGNAL_EXTRACTION, PROFILE_MATCHING)
    graph.add_edge(PROFILE_MATCHING, POLICY_EVALUATION)
    graph.add_edge(POLICY_EVALUATION, DECISION)
    graph.add_edge(DECISION, END)
    return graph


def compile_workflow_graph(
    *,
    extractor: SignalExtractor,
    matcher: ProfileMatcher,
    policy: DecisionPolicy,
    review_gate: HumanReviewGate | None,
    checkpointer: MemorySaver | None = None,
) -> CompiledStateGraph:
    return build_workflow_graph(
        extractor=extractor,
        matcher=matcher,
        policy=policy,
        review_gate=review_gate,
    ).compile(checkpointer=checkpointer or default_checkpointer())
