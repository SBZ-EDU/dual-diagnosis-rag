"""مدل امبدینگ چندزبانه (روی CPU کار می‌کند)."""
from __future__ import annotations
import numpy as np
from typing import List

_model = None


def get_model():
    """مدل امبدینگ را به‌صورت تنبل بارگذاری می‌کند (سینگلتون)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        import config
        _model = SentenceTransformer(config.EMBED_MODEL, device="cpu")
    return _model


def embed(texts: List[str]) -> np.ndarray:
    """متن‌ها را به بردار نرمال‌شده تبدیل می‌کند."""
    model = get_model()
    vecs = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)
    return vecs
