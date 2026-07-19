# Signal Extractor Evaluation

Golden dataset in [`dataset/`](dataset/) — human-curated `expected_signals` per job posting. Regex/deterministic extraction is tested separately in `tests/agents/test_agents.py`.

Each case JSON: `id`, `job_description`, `expected_signals` (+ optional `description`, `tags`).

## Run

```bash
poetry run pytest tests/eval/           # schema check only
poetry run pytest -m llm -s             # live LLM eval (OPENAI_API_KEY in .env)
```

Default `poetry run pytest` excludes `@pytest.mark.llm` tests.

## Metrics

Per field: precision, recall, F1 (set-based, case-insensitive). Aggregate: macro F1, exact match rate.

Runtime configs: [`app/runtime/configs/`](../app/runtime/configs/) — `v2` (LLM + prompt v1), `v3` (LLM + prompt v2).
