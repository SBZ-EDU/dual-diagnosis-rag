"""مدل مولدِ پاسخ (سبک، روی CPU). در صورت نبود مدل، به‌صورت استخراجی جواب می‌دهد."""
from __future__ import annotations
from typing import List, Dict
import logging

import config

log = logging.getLogger("generator")
_pipe = None
_load_tried = False
_load_ok = False

SYSTEM_PROMPT = (
    "تو یک دستیار بالینی فارسی‌زبان برای پروتکل درمان تشخیص دوگانه هستی "
    "(سایکوز + اعتیاد + BPD ± ADHD). فقط بر اساس متن مرجعِ ارائه‌شده پاسخ بده. "
    "اگر در متن نبود، صادقانه بگو اطلاع نداری. همیشه تأکید کن تصمیم نهایی با پزشک است."
)


def _load():
    global _pipe, _load_tried, _load_ok
    if _load_tried:
        return _load_ok
    _load_tried = True
    if not config.USE_GENERATOR:
        return False
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        log.info("بارگذاری مدل مولد: %s", config.GEN_MODEL)
        has_cuda = torch.cuda.is_available()
        device = "cuda" if has_cuda else "cpu"
        dtype = torch.float16 if has_cuda else torch.bfloat16  # bfloat16 روی CPU سبک‌تر و پشتیبانی‌شده
        tok = AutoTokenizer.from_pretrained(config.GEN_MODEL)
        model = AutoModelForCausalLM.from_pretrained(config.GEN_MODEL, torch_dtype=dtype)
        model.to(device)
        _pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tok,
            device=0 if has_cuda else -1,   # -1 یعنی CPU (بدون نیاز به accelerate)
        )
        _load_ok = True
    except Exception as e:  # نباید اپ را خراب کند
        log.warning("بارگذاری مدل مولد ناموفق بود → حالت استخراجی: %s", e)
        _pipe = None
        _load_ok = False
    return _load_ok


def build_prompt(query: str, contexts: List[Dict]) -> str:
    ctx = "\n\n".join(f"[مرجع {i+1}] ({c['source']})\n{c['text']}" for i, c in enumerate(contexts))
    return (
        f"{SYSTEM_PROMPT}\n\n=== مراجع ===\n{ctx}\n\n=== سؤال ===\n{query}\n\n=== پاسخ (فارسی) ==="
    )


def extractive_answer(query: str, contexts: List[Dict]) -> str:
    """جواب بدون LLM: فقط مراجع مرتبط را مرتب می‌چیند."""
    if not contexts:
        return "متأسفم، در پایگاه دانش فعلی پاسخی برای این سؤال پیدا نشد."
    lines = [f"📌 بر اساس {len(contexts)} قطعه‌ی مرتبط:"]
    for i, c in enumerate(contexts, 1):
        snippet = c["text"].strip().replace("\n", " ")
        if len(snippet) > 360:
            snippet = snippet[:360] + "…"
        lines.append(f"\n{i}) ({c['source']} — نوع: {c['type']})\n{snippet}")
    lines.append("\n\n⚠️ این پاسخ از متن پایگاه دانش استخراج شده؛ تصمیم نهایی درمان با پزشک است.")
    return "\n".join(lines)


def generate(query: str, contexts: List[Dict]) -> Dict:
    """یک پاسخ تولید می‌کند. خروجی شامل متن و روش استفاده‌شده است."""
    if not contexts:
        return {"text": "در پایگاه دانش پاسخی پیدا نشد.", "method": "no_context"}
    if not _load():
        return {"text": extractive_answer(query, contexts), "method": "extractive"}
    try:
        prompt = build_prompt(query, contexts)
        out = _pipe(prompt, max_new_tokens=config.MAX_NEW_TOKENS,
                    do_sample=True, temperature=0.3, top_p=0.9,
                    return_full_text=False, pad_token_id=_pipe.tokenizer.eos_token_id)
        text = out[0]["generated_text"].strip()
        return {"text": text, "method": "llm"}
    except Exception as e:
        log.warning("تولید LLM شکست خورد → استخراجی: %s", e)
        return {"text": extractive_answer(query, contexts), "method": "extractive_fallback"}
