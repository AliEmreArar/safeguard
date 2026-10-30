from reid_guardrail.pricing import estimate_cost


def test_cached_tokens_and_reasoning_are_counted_once():
    result = estimate_cost([{"usage": {"input_tokens": 100000, "output_tokens": 10000,
                                      "input_tokens_details": {"cached_tokens": 20000},
                                      "output_tokens_details": {"reasoning_tokens": 9000}}}], "grok-4.7")
    assert result["estimated_usd"] == 0.23


def test_unknown_model_and_large_context_have_no_guessed_price():
    assert estimate_cost([], "unknown")["estimated_usd"] is None
    assert estimate_cost([{"usage": {"input_tokens": 200001, "output_tokens": 1}}], "grok-4.7")["estimated_usd"] is None


def test_missing_usage_is_exposed():
    result = estimate_cost([{}, {"usage": {"input_tokens": 1000, "output_tokens": 100}}], "grok-4.7")
    assert result["outcomes_without_usage"] == 1
    assert result["estimated_usd"] == 0.0026
