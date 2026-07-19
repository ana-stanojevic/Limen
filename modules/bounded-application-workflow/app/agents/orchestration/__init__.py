from app.agents.contracts import WorkflowOrchestratorOutput
from app.agents.orchestration.state import WorkflowGraphState

# Resolve the forward ref on WorkflowOrchestratorOutput.run without importing
# graph/contracts in a cycle at contracts-import time.
WorkflowOrchestratorOutput.model_rebuild(
    _types_namespace={"WorkflowGraphState": WorkflowGraphState}
)


def __getattr__(name: str):
    if name == "DefaultWorkflowOrchestrator":
        from app.agents.orchestration.orchestrator import DefaultWorkflowOrchestrator

        return DefaultWorkflowOrchestrator
    if name == "build_workflow_graph":
        from app.agents.orchestration.graph import build_workflow_graph

        return build_workflow_graph
    if name == "compile_workflow_graph":
        from app.agents.orchestration.graph import compile_workflow_graph

        return compile_workflow_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DefaultWorkflowOrchestrator",
    "WorkflowGraphState",
    "build_workflow_graph",
    "compile_workflow_graph",
]
