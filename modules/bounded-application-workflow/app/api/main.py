from fastapi import FastAPI

from app.agents import WorkflowOrchestrator, WorkflowOrchestratorInput, create_agents
from app.domain.models import WorkflowInput, WorkflowOutput
from app.observability import instrument_app


def create_app(*, orchestrator: WorkflowOrchestrator | None = None) -> FastAPI:
    """HTTP app; `/workflow/run` always goes through the graph-backed orchestrator."""
    app = FastAPI(
        title="Bounded Application Workflow",
        description="Evaluate opportunities against a user profile.",
        version="0.1.0",
    )
    instrument_app(app)
    workflow = orchestrator or create_agents()[-1]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/workflow/run", response_model=WorkflowOutput)
    def run_workflow(workflow_input: WorkflowInput) -> WorkflowOutput:
        return workflow.run(
            WorkflowOrchestratorInput(workflow_input=workflow_input)
        ).output

    return app


app = create_app()
