"""بازیابی قطعه‌های مرتبط از پایگاه دانش."""
from __future__ import annotations
from typing import List, Dict
import numpy as np

import config
from . import embeddings, store


def retrieve(query: str, top_k: int | None = None) -> List[Dict]:
    """query را جست‌وجو می‌کند و قطعه‌های مرتبط برمی‌گرداند."""
    top_k = top_k or config.TOP_K
    chunks, vectors = store.load()
    if not chunks:
        return []
    q_vec = embeddings.embed([query])[0]
    q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-9)
    idxs = store.search(q_vec, vectors, top_k)
    return [{"text": chunks[i]["text"], "source": chunks[i].get("source", "?"),
             "type": chunks[i].get("type", "?"), "score": float((vectors[i] @ q_vec))}
            for i in idxs]
