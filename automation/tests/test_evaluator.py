from automation.modules.evaluator_groq import evaluate_response


def test_evaluator_rejects_short_text():
    result = evaluate_response("todo")
    assert result.approved is False
    assert result.repair_prompt is not None


def test_evaluator_accepts_normal_text():
    result = evaluate_response(
        "This is a complete and useful answer for production use."
    )
    assert result.approved is True
