"""ذخیره‌ی قطعه‌ها و بردارها + بازیابی با شباهت کسینوسی (بدون وابستگی سنگین)."""
from __future__ import annotations
import os
import json
import numpy as np
from typing import List, Dict, Tuple
import config


def save(chunks: List[Dict], vectors: np.ndarray) -> None:
    os.makedirs(config.INDEX_DIR, exist_ok=True)
    with open(config.CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    np.savez_compressed(config.VECTORS_FILE, vectors=vectors)


def load() -> Tuple[List[Dict], np.ndarray]:
    if not (os.path.exists(config.CHUNKS_FILE) and os.path.exists(config.VECTORS_FILE)):
        return [], np.zeros((0, 1), dtype=np.float32)
    with open(config.CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    data = np.load(config.VECTORS_FILE)
    vectors = data["vectors"].astype(np.float32)
    return chunks, vectors


def exists() -> bool:
    return os.path.exists(config.CHUNKS_FILE) and os.path.exists(config.VECTORS_FILE)


def search(query_vec: np.ndarray, vectors: np.ndarray, top_k: int) -> List[int]:
    """اندیس‌های top-k را بر اساس کسینوس (بردارها نرمال‌شده‌اند) برمی‌گرداند."""
    if vectors.shape[0] == 0:
        return []
    sims = vectors @ query_vec  # (n,)
    k = min(top_k, sims.shape[0])
    # k مورد پرشیارتر
    idx = np.argpartition(-sims, k - 1)[:k]
    idx = idx[np.argsort(-sims[idx])]
    return idx.tolist()
