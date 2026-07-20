from app.agents.contracts import (
    DecisionPolicy,
    ProfileMatcher,
    SignalExtractor,
    WorkflowOrchestratorInput,
    WorkflowOrchestratorOutput,
    WorkflowPlanner,
    WorkflowPlannerInput,
)
from app.agents.decision_rules import DefaultDecisionPolicy
from app.agents.human_review import approve_escalation
from app.agents.orchestration.runner import (
    execute_workflow_pipeline,
    resume_workflow_pipeline,
)
from app.agents.profile_matching import DefaultProfileMatcher
from app.agents.signal_extraction import DefaultSignalExtractor
from app.agents.workflow_planning import DefaultWorkflowPlanner


class DefaultWorkflowOrchestrator:
    def __init__(
        self,
        *,
        planner: WorkflowPlanner | None = None,
        extractor: SignalExtractor | None = None,
        matcher: ProfileMatcher | None = None,
        policy: DecisionPolicy | None = None,
        auto_approve_escalations: bool = True,
    ) -> None:
        self._planner = planner or DefaultWorkflowPlanner()
        self._extractor = extractor or DefaultSignalExtractor()
        self._matcher = matcher or DefaultProfileMatcher()
        self._policy = policy or DefaultDecisionPolicy()
        self._auto_approve_escalations = auto_approve_escalations

    def run(
        self, agent_input: WorkflowOrchestratorInput
    ) -> WorkflowOrchestratorOutput:
        plan = self._planner.run(
            WorkflowPlannerInput(workflow_input=agent_input.workflow_input)
        ).plan
        result = execute_workflow_pipeline(
            agent_input.workflow_input,
            plan=plan,
            extractor=self._extractor,
            matcher=self._matcher,
            policy=self._policy,
        )
        if result.review_interrupt is not None:
            if not self._auto_approve_escalations:
                interrupt = result.review_interrupt
                raise RuntimeError(
                    f"Paused at human_review for {result.workflow_id}: "
                    f"{interrupt.reason!r}. Resume with resume_workflow_pipeline(...)."
                )
            result = resume_workflow_pipeline(
                result,
                approve_escalation(
                    result.review_interrupt.decision,
                    requested_at=result.review_interrupt.requested_at,
                ),
            )
        if result.state.output is None:
            raise RuntimeError("Workflow completed without output")
        return WorkflowOrchestratorOutput(output=result.state.output, run=result.state)
