import pytest

from app.evaluation import (
    compare_runs,
    format_comparison_report,
    format_report,
    load_eval_cases,
    run_evaluation,
)
from app.local_env import get_local_env

MIN_LLM_MACRO_F1 = 0.5


@pytest.fixture
def openai_api_key():
    key = get_local_env("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set in .env")
    return key


def test_golden_dataset_loads():
    cases = load_eval_cases()
    assert len(cases) >= 7
    assert all(case.id and case.job_description.title for case in cases)


@pytest.mark.llm
def test_llm_signal_extractor_v2_against_golden_dataset(openai_api_key):
    run = run_evaluation(runtime_version="v2", progress=True)
    report = format_report(run)
    print(f"\n{report}")
    assert run.aggregate.macro_f1 >= MIN_LLM_MACRO_F1, report


@pytest.mark.llm
def test_llm_prompt_v3_vs_v2_comparison(openai_api_key):
    baseline = run_evaluation(label="prompt_v1", runtime_version="v2", progress=True)
    candidate = run_evaluation(label="prompt_v2", runtime_version="v3", progress=True)
    comparison = compare_runs(baseline, candidate)
    report = format_comparison_report(baseline, candidate, comparison)
    print(f"\n{report}")
    assert candidate.aggregate.macro_f1 >= MIN_LLM_MACRO_F1, report
