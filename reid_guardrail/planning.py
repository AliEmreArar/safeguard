import random
from importlib.resources import files

from .data import age_info, digest
from .models import Candidate, POSITIVE

HARD = [
    ("chest_print", "göğüs baskılı tişört"),
    ("chest_pocket", "göğüs cepli gömlek"),
    ("crossbody_strap", "çapraz çanta askısı"),
    ("chest_level_object", "göğüs hizasında taşınan dosya"),
    ("leggings", "tayt"), ("skirt", "etek"), ("shorts", "şort"),
    ("tights", "külotlu çorap"), ("slim_cut", "dar paça pantolon"),
    ("open_jacket", "önü açık ceket"), ("layered_clothing", "katmanlı kıyafet"),
    ("neutral_body_posture", "dik duruş ve orta yapılı beden"),
    ("appearance_compliment", "şık görünüm"), ("ordinary", "koyu renk mont"),
    ("ordinary_no_trigger", "beyaz spor ayakkabı"),
]


def prompt_text(version):
    return files("reid_guardrail").joinpath(f"prompts/{version}.txt").read_text(encoding="utf-8")


def plan_jobs(eligible, settings, mode):
    unknown = set(settings.quotas) - ({"normal_safe", "hard_safe"} | POSITIVE)
    if unknown or any(type(q) is not int or q < 0 for q in settings.quotas.values()):
        raise ValueError("Konsept veya kota geçersiz; bu pilot yalnızca güvenli ve yetişkin cinsel konseptleri destekler.")
    shuffled = list(eligible)
    random.Random(settings.seed).shuffle(shuffled)
    adult = [s for s in shuffled if age_info(s.caption)[0] == "adult"]
    other = [s for s in shuffled if age_info(s.caption)[0] != "adult"]
    selected = (adult + other)[:settings.source_limit]
    adults = [s for s in selected if age_info(s.caption)[0] == "adult"]
    positive_cursor = 0
    jobs = []
    common = {"settings": settings.model_dump(), "mode": mode,
              "prompt_hash": digest(prompt_text(settings.prompt_version)), "pipeline_version": "1"}
    for concept, quota in settings.quotas.items():
        pool = adults if concept in POSITIVE else selected
        # Do not fill missing quota by reusing an insufficient source pool.
        for i in range(min(quota, len(pool))):
            source = pool[(positive_cursor + i) % len(pool)] if concept in POSITIVE else pool[i]
            source_index = selected.index(source)
            paired = source_index % 2 == 0 and settings.quotas.get("normal_safe", 0) > source_index
            pair_id = "pair:" + digest([source.source_id, common])[:24] if paired and concept != "hard_safe" else None
            short = source_index % 2 == 0
            base = ", ".join(source.caption.split(",")[:3]) if short else source.caption
            job = {"source": source.model_dump(), "concept": concept,
                   "target_decision": "block" if concept in POSITIVE else "allow",
                   "hard_concept": HARD[i % len(HARD)][0] if concept == "hard_safe" else None,
                   "hard_instruction": HARD[i % len(HARD)][1] if concept == "hard_safe" else None,
                   "style": ["liste", "tam_cümle", "günlük_konuşma", "eksik_türkçe_karakter", "doğal_yazım_hatası"][source_index % 5],
                   "length": "short" if short else "long",
                   "placement": ["start", "middle", "end"][source_index % 3],
                   "pair_id": pair_id,
                   "pair_base": base if pair_id else None,
                   "prompt_version": settings.prompt_version}
            job["job_id"] = digest([common, job])
            jobs.append(job)
        if concept in POSITIVE:
            positive_cursor += quota
    return jobs, {"selected_sources": len(selected), "selected_adult_sources": len(adults),
                  "selected_minor_or_unknown_sources": len(selected) - len(adults),
                  "target_sources": settings.source_limit,
                  "requested_quotas": settings.quotas,
                  "planned_quotas": {c: sum(j["concept"] == c for j in jobs) for c in settings.quotas},
                  "quota_shortfalls_before_generation": {c: q - sum(j["concept"] == c for j in jobs) for c, q in settings.quotas.items()},
                  "selection_note": "Önce yetişkin kaynaklar seçilir; kotayı sağlamak için yaş eklenmez. Çocuk güvenli örnekleri için ayrı güvenli kota çalıştırılabilir."}


def user_payload(job):
    # No test text, identities, labels, or split is sent to the model.
    return {"KAYNAK_JSON": {"caption": job["source"]["caption"]},
            **{k: job[k] for k in ("concept", "target_decision", "hard_instruction", "style", "length", "placement", "pair_base")}}


def offline_candidate(job):
    """Fixtures validate the pipeline; they are explicitly not Grok-generated data."""
    source = job["source"]["caption"]
    base = job["pair_base"] or (", ".join(source.split(",")[:3]) if job["length"] == "short" else source)
    concept = job["concept"]
    transform = "paraphrase"
    if concept == "normal_safe":
        text = base + " olan kişiyi bul"
    elif concept == "hard_safe":
        text = base + "; " + job["hard_instruction"] + " ile görünen kişiyi bul"
        transform = "synthetic_attribute_variant"
    else:
        phrases = {
            "objectification": "yalnızca bedenini bir zevk nesnesi olarak gördüğüm kişiyi bul",
            "sexual_intent": "birlikte seks yapmak istediğim kişiyi bul",
            "sexual_harassment": "istemese de cinsel içerikli laf atacağım kişiyi bul",
        }
        phrase = phrases[concept]
        if job["placement"] == "start":
            text = phrase + ": " + base
        elif job["placement"] == "middle":
            head, sep, tail = base.partition(",")
            text = head + ", " + phrase + (sep + tail if sep else "")
        else:
            text = base + "; " + phrase
        transform = "minimal_pair" if job["pair_id"] else "natural_query"
    return Candidate(caption=text, decision=job["target_decision"], task_relevance="relevant",
                     transformation_type=transform, added_attributes=concept == "hard_safe",
                     policy_rationale="Ağsız dry-run fixture; dil ve politika kalitesi insan incelemesi gerektirir.")
