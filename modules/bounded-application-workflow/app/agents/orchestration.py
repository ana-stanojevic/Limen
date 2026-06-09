from collections.abc import Callable
from typing import TypeVar

from app.agents.contracts import (
    DecisionPolicy,
    DecisionPolicyInput,
    DecisionPolicyOutput,
    HumanReviewGate,
    HumanReviewGateInput,
    HumanReviewGateOutput,
    ProfileMatcher,
    ProfileMatcherInput,
    ProfileMatcherOutput,
    SignalExtractor,
    SignalExtractorInput,
    SignalExtractorOutput,
    WorkflowOrchestrator,
    WorkflowOrchestratorInput,
    WorkflowOrchestratorOutput,
    WorkflowPlanner,
    WorkflowPlannerInput,
    WorkflowPlannerOutput,
)
from app.agents.decision_rules import build_workflow_decision
from app.agents.profile_matching import match_profile_to_job
from app.agents.signal_extraction import extract_job_signals, focus_job_signals
from app.agents.workflow_planning import build_workflow_plan
from app.domain.job_signals import JobSignals
from app.domain.models import (
    DecisionType,
    EvaluationBrief,
    ProfileMatchResult,
    WorkflowDecision,
    WorkflowInput,
    WorkflowOutput,
)
from app.domain.workflow_run import WorkflowEventType, WorkflowPlan, WorkflowRun
from app.domain.workflow_state import WorkflowState
from app.text import dedupe_strings

I = TypeVar("I")
O = TypeVar("O")

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


def _agent(name: str, fn: Callable[[I], O]) -> type:
    return type(name, (), {"run": lambda self, agent_input: fn(agent_input)})


DefaultSignalExtractor = _agent(
    "DefaultSignalExtractor",
    lambda i: SignalExtractorOutput(
        signals=extract_job_signals(i.job_description, i.required_signals or None)
    ),
)
DefaultProfileMatcher = _agent(
    "DefaultProfileMatcher",
    lambda i: ProfileMatcherOutput(
        match=match_profile_to_job(
            i.user_profile,
            i.job_description,
            i.signals,
            required_signals=i.required_signals or None,
        )
    ),
)
DefaultDecisionPolicy = _agent(
    "DefaultDecisionPolicy",
    lambda i: DecisionPolicyOutput(
        decision=build_workflow_decision(i.match, i.signals, i.plan)
    ),
)
DefaultWorkflowPlanner = _agent(
    "DefaultWorkflowPlanner",
    lambda i: WorkflowPlannerOutput(plan=build_workflow_plan(i.workflow_input)),
)
PassthroughHumanReviewGate = _agent(
    "PassthroughHumanReviewGate",
    lambda i: HumanReviewGateOutput(decision=i.decision, approved=True),
)


def build_evaluation_brief(
    plan: WorkflowPlan,
    match: ProfileMatchResult,
    decision: WorkflowDecision,
    signals: JobSignals,
) -> EvaluationBrief:
    findings = dedupe_strings(
        list(decision.reasons)
        + list(decision.risks)
        + list(decision.missing_information)
    )
    return EvaluationBrief(
        evaluation_focus=list(plan.evaluation_focus),
        signal_highlights=focus_job_signals(signals, plan.required_signals),
        findings=findings,
        decision=decision.decision,
        score=decision.score,
    )


class DefaultWorkflowOrchestrator:
    def __init__(
        self,
        *,
        planner: WorkflowPlanner | None = None,
        extractor: SignalExtractor | None = None,
        matcher: ProfileMatcher | None = None,
        policy: DecisionPolicy | None = None,
        review_gate: HumanReviewGate | None = None,
    ) -> None:
        self._planner = planner or DefaultWorkflowPlanner()
        self._extractor = extractor or DefaultSignalExtractor()
        self._matcher = matcher or DefaultProfileMatcher()
        self._policy = policy or DefaultDecisionPolicy()
        self._review_gate = review_gate or PassthroughHumanReviewGate()

    def run(
        self, agent_input: WorkflowOrchestratorInput
    ) -> WorkflowOrchestratorOutput:
        output, run = _run_stages(
            agent_input.workflow_input,
            planner=self._planner,
            extractor=self._extractor,
            matcher=self._matcher,
            policy=self._policy,
            review_gate=self._review_gate,
        )
        return WorkflowOrchestratorOutput(output=output, run=run)


def default_agents() -> tuple[
    SignalExtractor,
    ProfileMatcher,
    DecisionPolicy,
    HumanReviewGate,
    WorkflowPlanner,
    WorkflowOrchestrator,
]:
    extractor = DefaultSignalExtractor()
    matcher = DefaultProfileMatcher()
    policy = DefaultDecisionPolicy()
    review_gate = PassthroughHumanReviewGate()
    planner = DefaultWorkflowPlanner()
    orchestrator = DefaultWorkflowOrchestrator(
        planner=planner,
        extractor=extractor,
        matcher=matcher,
        policy=policy,
        review_gate=review_gate,
    )
    return extractor, matcher, policy, review_gate, planner, orchestrator


def evaluate_workflow(workflow_input: WorkflowInput) -> WorkflowOutput:
    *_, orchestrator = default_agents()
    return orchestrator.run(
        WorkflowOrchestratorInput(workflow_input=workflow_input)
    ).output


def run_workflow_evaluation(
    workflow_input: WorkflowInput,
) -> tuple[WorkflowOutput, WorkflowRun]:
    *_, orchestrator = default_agents()
    result = orchestrator.run(
        WorkflowOrchestratorInput(workflow_input=workflow_input)
    )
    return result.output, result.run


def _run_stages(
    workflow_input: WorkflowInput,
    *,
    planner: WorkflowPlanner,
    extractor: SignalExtractor,
    matcher: ProfileMatcher,
    policy: DecisionPolicy,
    review_gate: HumanReviewGate | None = None,
    plan: WorkflowPlan | None = None,
) -> tuple[WorkflowOutput, WorkflowRun]:
    profile = workflow_input.user_profile
    job = workflow_input.job_description
    if plan is None:
        plan = planner.run(
            WorkflowPlannerInput(workflow_input=workflow_input)
        ).plan
    run = WorkflowRun(input=workflow_input, plan=plan)
    run.record_event(
        WorkflowEventType.RUN_STARTED, WorkflowState.INTAKE, "Workflow run started."
    )

    signals: JobSignals | None = None
    match: ProfileMatchResult | None = None
    decision: WorkflowDecision | None = None

    for stage in plan.stages:
        if stage == WorkflowState.INTAKE:
            continue

        if stage == WorkflowState.HUMAN_REVIEW:
            if (
                not plan.requires_human_review
                or decision is None
                or decision.decision != DecisionType.ESCALATE
            ):
                continue
            run.transition_to(stage)
            if review_gate is not None:
                brief = build_evaluation_brief(plan, match, decision, signals)
                decision = review_gate.run(
                    HumanReviewGateInput(evaluation_brief=brief, decision=decision)
                ).decision
            continue

        if stage == WorkflowState.DECISION:
            brief = build_evaluation_brief(plan, match, decision, signals)
            company = job.company or "an unspecified company"
            output = WorkflowOutput(
                input_summary=(
                    f"{profile.name} is being evaluated for {job.title} at {company}."
                ),
                evaluation_brief=brief,
                decision=decision,
                job_signals=signals,
                recommended_next_steps=list(_NEXT_STEPS[decision.decision]),
            )
            run.complete(output)
            return output, run

        run.transition_to(stage)
        if stage == WorkflowState.SIGNAL_EXTRACTION:
            signals = extractor.run(
                SignalExtractorInput(
                    job_description=job, required_signals=plan.required_signals
                )
            ).signals
        elif stage == WorkflowState.PROFILE_MATCHING:
            match = matcher.run(
                ProfileMatcherInput(
                    user_profile=profile,
                    job_description=job,
                    signals=signals,
                    required_signals=plan.required_signals,
                )
            ).match
        elif stage == WorkflowState.POLICY_EVALUATION:
            decision = policy.run(
                DecisionPolicyInput(match=match, signals=signals, plan=plan)
            ).decision

    raise RuntimeError("Workflow plan did not include a decision stage.")
