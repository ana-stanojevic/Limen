import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.domain.job_signals import JobSignals
from app.domain.models import JobDescription

DEFAULT_DATASET_DIR = Path(__file__).resolve().parents[2] / "eval" / "dataset"


class EvalCase(BaseModel):
    id: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    job_description: JobDescription
    expected_signals: JobSignals


def load_eval_cases(dataset_dir: Path | None = None) -> list[EvalCase]:
    root = dataset_dir or DEFAULT_DATASET_DIR
    cases: list[EvalCase] = []

    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text())
        cases.append(EvalCase.model_validate(payload))

    if not cases:
        raise FileNotFoundError(f"No evaluation cases found in {root}")

    return cases
