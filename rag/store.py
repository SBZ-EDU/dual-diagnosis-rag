"""ذخیره‌ی قطعه‌ها و بردارها + بازیابی با شباهت کسینوسی (بدون وابستگی سنگین)."""
from __future__ import annotations
import hashlib
import os
import json
import numpy as np
from typing import List, Dict, Tuple
import config

# کش درون‌حافظه‌ای؛ قبلاً در هر پرس‌وجو chunks.json و vectors.npz از دیسک خوانده می‌شد
_cache: Dict[str, object] = {"key": None, "chunks": None, "vectors": None}


def _index_key() -> str:
    """کلید تغییر ایندکس بر اساس زمان تغییر فایل‌ها."""
    try:
        return (f"{os.path.getmtime(config.CHUNKS_FILE):.0f}:"
                f"{os.path.getmtime(config.VECTORS_FILE):.0f}:"
                f"{os.path.getsize(config.CHUNKS_FILE)}")
    except OSError:
        return ""


def save(chunks: List[Dict], vectors: np.ndarray) -> None:
    """ذخیره‌ی فشرده: JSON بدون تورفتگی + بردارهای float16 (نصف حجم).

    load() بردارها را به float32 برمی‌گرداند؛ دقت کسینوس در fp16 برای این
    کاربرد کافی است و حجم ایندکس حدوداً نصف می‌شود.
    """
    os.makedirs(config.INDEX_DIR, exist_ok=True)
    with open(config.CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    np.savez_compressed(config.VECTORS_FILE, vectors=vectors.astype(np.float16))
    _cache["key"] = None  # کش قدیمی را بی‌اعتبار کن


def load() -> Tuple[List[Dict], np.ndarray]:
    key = _index_key()
    if _cache["key"] == key and _cache["chunks"] is not None:
        return _cache["chunks"], _cache["vectors"]
    if not (os.path.exists(config.CHUNKS_FILE) and os.path.exists(config.VECTORS_FILE)):
        return [], np.zeros((0, 1), dtype=np.float32)
    with open(config.CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    data = np.load(config.VECTORS_FILE)
    vectors = data["vectors"].astype(np.float32)
    _cache.update(key=key, chunks=chunks, vectors=vectors)
    return chunks, vectors


def exists() -> bool:
    return os.path.exists(config.CHUNKS_FILE) and os.path.exists(config.VECTORS_FILE)


def search(query_vec: np.ndarray, vectors: np.ndarray, top_k: int) -> List[int]:
    """اندیس‌های top-k را بر اساس کسینوس (بردارها نرمال‌شده‌اند) برمی‌گرداند."""
    if vectors.shape[0] == 0:
        return []
    sims = vectors @ query_vec  # (n,)
    k = min(top_k, sims.shape[0])
    if k <= 0:
        return []
    # k مورد پرشیارتر
    idx = np.argpartition(-sims, k - 1)[:k]
    idx = idx[np.argsort(-sims[idx])]
    return idx.tolist()


# ---------- تازگی ایندکس نسبت به داده‌ها ----------
def data_manifest() -> str:
    """اثر انگشت منابع داده؛ اگر داده تغییر کند این مقدار تغییر می‌کند."""
    h = hashlib.sha256()
    paths = [config.PROTOCOL_FILE]
    for folder in config.SOURCES.values():
        if os.path.isdir(folder):
            for fname in sorted(os.listdir(folder)):
                p = os.path.join(folder, fname)
                if os.path.isfile(p) and not fname.startswith("."):
                    paths.append(p)
    for p in paths:
        try:
            h.update(p.encode("utf-8"))
            h.update(str(os.path.getmtime(p)).encode())
            h.update(str(os.path.getsize(p)).encode())
        except OSError:
            continue
    return h.hexdigest()[:16]


def manifest_file() -> str:
    return os.path.join(config.INDEX_DIR, "manifest.json")


def save_manifest() -> None:
    os.makedirs(config.INDEX_DIR, exist_ok=True)
    with open(manifest_file(), "w", encoding="utf-8") as f:
        json.dump({"data_manifest": data_manifest()}, f)


def manifest_matches() -> bool:
    """True اگر ایندکس موجود با داده‌های فعلی هم‌خوان باشد."""
    if not exists():
        return False
    try:
        with open(manifest_file(), "r", encoding="utf-8") as f:
            saved = json.load(f).get("data_manifest")
        return saved == data_manifest()
    except (OSError, ValueError):
        return False
