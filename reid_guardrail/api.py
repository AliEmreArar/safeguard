import asyncio
import json
import os
import random
import re

import httpx
from pydantic import ValidationError

from .models import Envelope
from .planning import prompt_text, user_payload


def redact(text, secret=""):
    text = str(text)
    if secret:
        text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"(?i)(authorization\s*[:=]\s*|bearer\s+)[^\s,;]+", r"\1[REDACTED]", text)
    return re.sub(r"\bxai-[A-Za-z0-9_-]+", "[REDACTED]", text)


class ApiFailure(Exception):
    def __init__(self, category, detail, usage=None, attempts=1):
        self.category = category
        self.detail = detail
        self.usage = usage or {}
        self.attempts = attempts


def request_body(job, settings):
    return {"model": settings.model, "store": False,
            "input": [{"role": "system", "content": prompt_text(settings.prompt_version)},
                      {"role": "user", "content": json.dumps(user_payload(job), ensure_ascii=False)}],
            "text": {"format": {"type": "json_schema", "name": "moderation_candidate",
                                "strict": True, "schema": Envelope.model_json_schema()}},
            "temperature": settings.temperature, "max_output_tokens": settings.max_output_tokens}


def parse_response(data, envelope_model=Envelope):
    usage = data.get("usage") or {}
    if data.get("status") == "incomplete":
        raise ApiFailure("incomplete_output", "Token limiti veya tamamlanmamış yanıt.", usage)
    if data.get("error"):
        # Raw server errors are deliberately not logged: they may echo prompts/secrets.
        raise ApiFailure("api_error", "API error alanı döndürdü.", usage)
    chunks = []
    output = data.get("output", [])
    if not isinstance(output, list):
        raise ApiFailure("invalid_schema", "API output alanı liste değil.", usage)
    for item in output:
        if not isinstance(item, dict) or not isinstance(item.get("content", []), list):
            raise ApiFailure("invalid_schema", "API message yapısı geçersiz.", usage)
        for part in item.get("content", []):
            if not isinstance(part, dict):
                raise ApiFailure("invalid_schema", "API content yapısı geçersiz.", usage)
            if part.get("type") == "refusal":
                raise ApiFailure("refusal", part.get("refusal", "API refusal"), usage)
            if part.get("type") == "output_text":
                if not isinstance(part.get("text", ""), str):
                    raise ApiFailure("invalid_schema", "API metin alanı string değil.", usage)
                chunks.append(part.get("text", ""))
    text = "".join(chunks)
    if not text.strip():
        raise ApiFailure("empty_output", "Yanıt metni boş.", usage)
    try:
        result = envelope_model.model_validate_json(text)
    except ValidationError:
        raise ApiFailure("invalid_schema", "Yanıt JSON şemasını karşılamıyor; ham çıktı loglanmadı.", usage) from None
    if result.status == "refused":
        raise ApiFailure("refusal", result.refusal_reason or "Üretici reddetti.", usage)
    if result.candidate is None or result.refusal_reason is not None:
        raise ApiFailure("invalid_schema", "status/candidate/refusal_reason tutarsız.", usage)
    return result.candidate, usage, data.get("model")


class GrokClient:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.key = os.environ.get("XAI_API_KEY", "")
        if not self.key:
            raise ValueError("XAI_API_KEY ortam değişkeni gerekli; .env yerelde desteklenir.")
        if not settings.model.strip():
            raise ValueError("Canlı üretim için --model veya XAI_MODEL gerekli.")
        self.client = httpx.AsyncClient(
            base_url="https://api.x.ai/v1/", timeout=settings.timeout_seconds,
            follow_redirects=False, transport=transport,
            headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"})

    async def close(self):
        await self.client.aclose()

    async def generate(self, job):
        for attempt in range(self.settings.max_retries + 1):
            try:
                response = await self.client.post("responses", json=request_body(job, self.settings))
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt < self.settings.max_retries:
                    await asyncio.sleep(min(2 ** attempt + random.random(), 8))
                    continue
                raise ApiFailure("network_error", "Ağ/timeout hatası; ham istek loglanmadı.", attempts=attempt + 1) from None
            status = response.status_code
            if status == 429 or status >= 500:
                if attempt < self.settings.max_retries:
                    try:
                        delay = min(max(float(response.headers.get("retry-after", "0")), 0), 30)
                    except ValueError:
                        delay = 0
                    await asyncio.sleep(max(delay, min(2 ** attempt + random.random(), 8)))
                    continue
            if status >= 400:
                category = "refusal" if status == 451 else "http_error"
                raise ApiFailure(category, f"HTTP {status}; ham hata gövdesi loglanmadı.", attempts=attempt + 1)
            try:
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError()
            except ValueError:
                raise ApiFailure("invalid_schema", "HTTP yanıtı JSON nesnesi değil.", attempts=attempt + 1) from None
            try:
                candidate, usage, model = parse_response(data)
            except ApiFailure as exc:
                exc.detail = redact(exc.detail, self.key)
                exc.attempts = attempt + 1
                raise
            return candidate, usage, model or self.settings.model, attempt + 1
