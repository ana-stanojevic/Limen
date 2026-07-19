from app.agents.contracts import WorkflowPlannerInput, WorkflowPlannerOutput
from app.agents.signal_extraction.deterministic import extract_job_signals
from app.agents.workflow_planning.plan import (
    DECISION,
    HUMAN_REVIEW,
    INTAKE,
    POLICY_EVALUATION,
    PROFILE_MATCHING,
    SIGNAL_EXTRACTION,
    WorkflowPlan,
)
from app.domain.job_signals import JobSignals
from app.domain.models import WorkflowInput

_CORE_STAGES = [
    INTAKE,
    SIGNAL_EXTRACTION,
    PROFILE_MATCHING,
    POLICY_EVALUATION,
]


def _predict_human_review(pre_scan: JobSignals) -> bool:
    # Decision rules escalate risky postings to review; mirror that here so the
    # plan anticipates the human_review stage instead of always omitting it.
    return bool(pre_scan.risk_indicators)


def create_workflow_plan(workflow_input: WorkflowInput) -> WorkflowPlan:
    """Estimate the stages of a run before executing it."""
    # Cheap pre-scan of the posting; the execution re-extracts signals inside
    # its own signal_extraction stage.
    pre_scan = extract_job_signals(workflow_input.job_description)

    stages = list(_CORE_STAGES)
    if _predict_human_review(pre_scan):
        stages.append(HUMAN_REVIEW)
    stages.append(DECISION)

    return WorkflowPlan(stages=stages)


class DefaultWorkflowPlanner:
    def run(self, agent_input: WorkflowPlannerInput) -> WorkflowPlannerOutput:
        plan = create_workflow_plan(agent_input.workflow_input)
        return WorkflowPlannerOutput(plan=plan)
