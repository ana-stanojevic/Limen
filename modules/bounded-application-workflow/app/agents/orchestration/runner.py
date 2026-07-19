from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from app.agents.contracts import (
    DecisionPolicy,
    HumanReviewGate,
    ProfileMatcher,
    SignalExtractor,
)
from app.agents.orchestration.graph import compile_workflow_graph
from app.agents.orchestration.state import WorkflowGraphState
from app.domain.models import WorkflowInput, WorkflowOutput
from app.agents.workflow_planning.plan import WorkflowPlan


def execute_workflow_pipeline(
    workflow_input: WorkflowInput,
    *,
    plan: WorkflowPlan,
    extractor: SignalExtractor,
    matcher: ProfileMatcher,
    policy: DecisionPolicy,
    review_gate: HumanReviewGate | None = None,
    graph: CompiledStateGraph | None = None,
    checkpointer: MemorySaver | None = None,
) -> tuple[WorkflowOutput, WorkflowGraphState]:
    """Run the workflow via LangGraph; return output + checkpointed graph state."""
    compiled = graph or compile_workflow_graph(
        extractor=extractor,
        matcher=matcher,
        policy=policy,
        review_gate=review_gate,
        checkpointer=checkpointer,
    )
    workflow_id = str(uuid4())
    initial = WorkflowGraphState.from_workflow_input(
        workflow_input,
        plan,
        workflow_id=workflow_id,
    )
    config = {"configurable": {"thread_id": workflow_id}}
    compiled.invoke(initial, config)

    restored = WorkflowGraphState.model_validate(compiled.get_state(config).values)
    if restored.output is None:
        raise RuntimeError("Checkpoint did not contain workflow output")
    return restored.output, restored
