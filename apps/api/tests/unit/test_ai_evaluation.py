from app.ai.evaluation.harness import EvaluationHarness


def test_ai_evaluation_golden_set_fast_tier() -> None:
    """Evaluation harness test running deterministically against recorded responses."""
    harness = EvaluationHarness()
    summary = harness.run_suite()

    assert summary.total >= 5
    assert summary.passed == summary.total
    assert summary.failed == 0
    assert summary.pass_rate == 100.0

    for result in summary.results:
        assert result.passed, f"Test {result.test_id} ({result.agent}) failed: {result.details}"
        assert result.score == 1.0


def test_ai_evaluation_detects_missing_medicine_failure() -> None:
    """Harness correctly identifies evaluation failures when model response is deficient."""
    harness = EvaluationHarness()

    deficient_item = {
        "id": "eval-fail-test",
        "agent": "visit_summarizer",
        "input": {"notes": "Prescribed Paracetamol 500mg"},
        "recorded_model_response": {
            "summary": "Checkup done",
            "medicines": [],  # missing expected medicine
            "advice": "Rest well",
        },
        "expected": {
            "contains_medicines": ["Paracetamol"],
        },
    }

    result = harness.evaluate_test_case(deficient_item)
    assert not result.passed
    assert result.score == 0.0
    assert result.details["missing_med_Paracetamol"] is True
