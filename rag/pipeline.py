"""خط لوله‌ی RAG: بازیابی + تولید + لاگ در W&B."""
from __future__ import annotations
import time
import logging
from typing import List, Dict, Optional

import config
from . import retriever, generator

log = logging.getLogger("rag")

# ---------- W&B (اختیاری) ----------
_wandb = None
_wandb_init_tried = False


def _wandb_init():
    global _wandb, _wandb_init_tried
    if _wandb_init_tried:
        return _wandb
    _wandb_init_tried = True
    if not config.WANDB_ENABLED:
        return None
    try:
        import wandb
        wandb.init(
            project=config.WANDB_PROJECT,
            entity=config.WANDB_ENTITY,
            job_type="rag_inference",
            config={
                "embed_model": config.EMBED_MODEL,
                "gen_model": config.GEN_MODEL,
                "top_k": config.TOP_K,
                "chunk_size": config.CHUNK_SIZE,
            },
            reinit=True,
        )
        _wandb = wandb
        log.info("W&B متصل شد: %s/%s", config.WANDB_ENTITY, config.WANDB_PROJECT)
    except Exception as e:
        log.warning("اتصال W&B ناموفق بود (ادامه بدون لاگ): %s", e)
        _wandb = None
    return _wandb


def answer(question: str, top_k: Optional[int] = None) -> Dict:
    """پاسخ کامل به یک سؤال: شامل بازیابی، تولید و متادیتا."""
    t0 = time.time()
    contexts = retriever.retrieve(question, top_k=top_k)
    t_ret = time.time() - t0

    t1 = time.time()
    gen = generator.generate(question, contexts)
    t_gen = time.time() - t1

    result = {
        "question": question,
        "answer": gen["text"],
        "method": gen["method"],
        "sources": [{"source": c["source"], "type": c["type"], "score": round(c["score"], 4)}
                    for c in contexts],
        "contexts": [c["text"] for c in contexts],
        "latency": {"retrieve_s": round(t_ret, 3), "generate_s": round(t_gen, 3)},
    }

    # لاگ در W&B
    wb = _wandb_init()
    if wb is not None:
        try:
            wb.log({
                "query_len": len(question),
                "num_sources": len(contexts),
                "top_score": contexts[0]["score"] if contexts else 0.0,
                "method": gen["method"],
                "retrieve_s": t_ret,
                "generate_s": t_gen,
                "question": question[:500],
            })
        except Exception as e:
            log.warning("لاگ W&B شکست خورد: %s", e)

    return result


def add_feedback(question: str, answer_text: str, rating: int, comment: str = "") -> str:
    """بازخورد کاربر را ذخیره می‌کند تا بعداً در آموزش/بهبود استفاده شود."""
    import os, json, datetime, uuid
    os.makedirs(config.SOURCES["feedback"], exist_ok=True)
    rec = {
        "id": uuid.uuid4().hex[:8],
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "question": question,
        "answer": answer_text,
        "rating": int(rating),
        "comment": comment,
    }
    path = os.path.join(config.SOURCES["feedback"], f"fb_{rec['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return path
