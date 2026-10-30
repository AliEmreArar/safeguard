"""This test is never run by default and incurs one API call only with explicit opt-in."""
import asyncio
import os

import pytest

from reid_guardrail.api import GrokClient
from reid_guardrail.models import Settings
from reid_guardrail.planning import plan_jobs
from reid_guardrail.data import Source


@pytest.mark.live
@pytest.mark.skipif(os.environ.get("RUN_XAI_LIVE_TESTS") != "1", reason="Açık canlı test etkinleştirmesi gerekli")
def test_live_safe_candidate():
    settings = Settings(model=os.environ["XAI_MODEL"], source_limit=1, quotas={"normal_safe": 1})
    source = Source(caption="30 yaşında, mavi ceketli kişi", split="train", labels=["safe"], source_id="fixture:1", metadata={})
    jobs, _ = plan_jobs([source], settings, "live")
    async def check():
        client = GrokClient(settings)
        try:
            candidate, usage, model, attempts = await client.generate(jobs[0])
            assert candidate.caption and model and attempts == 1
        finally:
            await client.close()
    asyncio.run(check())
