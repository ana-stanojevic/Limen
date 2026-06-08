from app.domain.job_signals import JobSignals, SignalCategory


def test_job_signals_defaults_to_empty_lists():
    signals = JobSignals()

    assert signals.required_skills == []
    assert signals.preferred_skills == []
    assert signals.seniority_signals == []
    assert signals.production_expectations == []
    assert signals.risk_indicators == []
    assert signals.missing_signals == []


def test_signal_category_covers_job_signals_fields():
    categories = {category.value for category in SignalCategory}

    assert categories == {
        "required_skills",
        "preferred_skills",
        "seniority_signals",
        "production_expectations",
        "risk_indicators",
        "missing_signals",
    }
