"""Dated official pricing snapshot; unknown models are never assigned guessed prices."""

PRICING_SOURCE = "https://docs.x.ai/developers/models/grok-4.7"
VERIFIED_ON = "2026-10-27"


def estimate_cost(outcomes, requested_model):
    if requested_model != "grok-4.7":
        return {"estimated_usd": None, "reason": "Bu model için doğrulanmış fiyat yok."}
    total = 0.0
    measured = 0
    missing = 0
    cached_tokens = 0
    for item in outcomes:
        usage = item.get("usage") or {}
        if not usage:
            missing += 1
            continue
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        cached = (usage.get("input_tokens_details") or {}).get("cached_tokens", 0)
        if not all(type(n) is int and n >= 0 for n in (input_tokens, output_tokens, cached)) or cached > input_tokens:
            return {"estimated_usd": None, "reason": "Kullanım sayaçları geçersiz veya eksik."}
        if input_tokens > 200000:
            return {"estimated_usd": None, "reason": "Uzun bağlam fiyatı bu snapshot içinde doğrulanmadı."}
        # output_tokens already includes reasoning_tokens; do not count reasoning twice.
        total += ((input_tokens - cached) * 2.0 + cached * 0.5 + output_tokens * 6.0) / 1000000
        cached_tokens += cached
        measured += 1
    return {"estimated_usd": round(total, 6) if measured else None,
            "requested_model": requested_model, "source": PRICING_SOURCE,
            "verified_on": VERIFIED_ON,
            "usd_per_million_tokens": {"uncached_input": 2.0, "cached_input": 0.5, "output_including_reasoning": 6.0},
            "outcomes_with_usage": measured, "outcomes_without_usage": missing,
            "cached_input_tokens": cached_tokens,
            "note": "Yalnızca API'nin bildirdiği token sayaçlarına dayalı tahmin; fatura değildir. Bildirilmeyen/timeout kullanımı ve ayrı canlı pytest dahil değildir."}
