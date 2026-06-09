from app.agents.contracts import (
    DecisionPolicy,
    DecisionPolicyInput,
    HumanReviewGate,
    HumanReviewGateInput,
    ProfileMatcher,
    ProfileMatcherInput,
    SignalExtractor,
    SignalExtractorInput,
    WorkflowPlanner,
    WorkflowPlannerInput,
)
from app.agents.evaluation_brief import build_evaluation_brief
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
from app.domain.workflow_run import WorkflowEventType, WorkflowPlan, WorkflowRun
from app.domain.workflow_state import WorkflowState

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


def _input_summary(profile: UserProfile, job: JobDescription) -> str:
    company = job.company or "an unspecified company"
    return (
        f"{profile.name} is being evaluated for {job.title} at {company}."
    )


def _should_run_human_review(
    plan: WorkflowPlan, decision: WorkflowDecision | None
) -> bool:
    if WorkflowState.HUMAN_REVIEW not in plan.stages:
        return False
    if decision is None:
        return False
    return decision.decision == DecisionType.ESCALATE


def run_workflow_evaluation(
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
        WorkflowEventType.RUN_STARTED,
        WorkflowState.INTAKE,
        "Workflow run started.",
    )

    signals: JobSignals | None = None
    match: ProfileMatchResult | None = None
    decision: WorkflowDecision | None = None

    for stage in plan.stages:
        if stage == WorkflowState.INTAKE:
            continue

        if stage == WorkflowState.HUMAN_REVIEW:
            if not _should_run_human_review(plan, decision):
                continue
            run.transition_to(stage)
            evaluation_brief = build_evaluation_brief(plan, match, decision, signals)
            if review_gate is not None:
                review_result = review_gate.run(
                    HumanReviewGateInput(
                        evaluation_brief=evaluation_brief,
                        decision=decision,
                    )
                )
                decision = review_result.decision
            continue

        if stage == WorkflowState.DECISION:
            evaluation_brief = build_evaluation_brief(plan, match, decision, signals)
            output = WorkflowOutput(
                input_summary=_input_summary(profile, job),
                evaluation_brief=evaluation_brief,
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
                    job_description=job,
                    required_signals=plan.required_signals,
                )
            ).signals
        elif stage == WorkflowState.PROFILE_MATCHING:
            match = matcher.run(
                ProfileMatcherInput(
                    user_profile=profile,
                    job_description=job,
                    signals=signals,
                )
            ).match
        elif stage == WorkflowState.POLICY_EVALUATION:
            decision = policy.run(
                DecisionPolicyInput(match=match, signals=signals)
            ).decision

    raise RuntimeError("Workflow plan did not include a decision stage.")


def evaluate_workflow(
    workflow_input: WorkflowInput,
    *,
    planner: WorkflowPlanner,
    extractor: SignalExtractor,
    matcher: ProfileMatcher,
    policy: DecisionPolicy,
    review_gate: HumanReviewGate | None = None,
    plan: WorkflowPlan | None = None,
) -> WorkflowOutput:
    output, _ = run_workflow_evaluation(
        workflow_input,
        planner=planner,
        extractor=extractor,
        matcher=matcher,
        policy=policy,
        review_gate=review_gate,
        plan=plan,
    )
    return output
