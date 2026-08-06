"""شکستن متن پایگاه دانش به قطعه‌های قابل‌بازیابی و بارگذاری اسناد اضافه."""
from __future__ import annotations
import os
import json
import re
from typing import List, Dict
import config


def _split_markdown_by_headers(text: str) -> List[str]:
    """متن مارک‌داون را بر اساس سرتیترها به قطعه‌ی معنادار می‌شکند."""
    lines = text.splitlines()
    chunks: List[str] = []
    buffer: List[str] = []

    def flush():
        if buffer:
            block = "\n".join(buffer).strip()
            if block:
                chunks.append(block)
            buffer.clear()

    for line in lines:
        if re.match(r"^#{1,4}\s", line):
            flush()
        buffer.append(line)
    flush()
    return chunks


def _chunk_text(text: str, size: int, overlap: int) -> List[str]:
    """شکستن یک بلوک بلند به قطعه‌های هم‌پوشان بر اساس کاراکتر."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    out: List[str] = []
    step = max(1, size - overlap)
    for i in range(0, len(text), step):
        piece = text[i:i + size].strip()
        if piece:
            out.append(piece)
        if i + size >= len(text):
            break
    return out


def load_documents() -> List[Dict]:
    """همه‌ی منابع (پروتکل + مقالات + سابقه بیمار + بازخورد) را بارگذاری می‌کند."""
    docs: List[Dict] = []

    # ۱) پروتکل اصلی
    if os.path.exists(config.PROTOCOL_FILE):
        with open(config.PROTOCOL_FILE, "r", encoding="utf-8") as f:
            protocol = f.read()
        for block in _split_markdown_by_headers(protocol):
            for piece in _chunk_text(block, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                docs.append({"source": "protocol.md", "type": "protocol", "text": piece})

    # ۲) منابع اضافه از پوشه‌ها
    type_map = {"articles": "article", "guidelines": "guideline", "patient_history": "patient", "feedback": "feedback"}
    for folder, kind in type_map.items():
        d = config.SOURCES[folder]
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            path = os.path.join(d, fname)
            if not os.path.isfile(path) or fname.startswith("."):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
            except Exception:
                continue
            # مقاله‌های اعتبارسنجی‌شده JSON/JSONL به متن ساخت‌یافته RAG تبدیل می‌شوند.
            records = []
            try:
                if fname.endswith(".jsonl"):
                    records = [json.loads(x) for x in raw.splitlines() if x.strip()]
                elif fname.endswith(".json"):
                    obj = json.loads(raw)
                    if isinstance(obj, dict) and isinstance(obj.get("articles"), list):
                        records = obj["articles"]
                    elif isinstance(obj, list):
                        records = obj
                    elif isinstance(obj, dict) and obj.get("title"):
                        records = [obj]
                    else:
                        records = []
            except Exception:
                records = []
            if records:
                for rec in records:
                    text = "\n".join(filter(None, [rec.get("title"), rec.get("abstract"), rec.get("journal"), rec.get("published"), rec.get("url")]))
                    for piece in _chunk_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                        docs.append({"source": rec.get("url") or fname, "type": kind, "text": piece})
                continue
            for block in _split_markdown_by_headers(raw):
                for piece in _chunk_text(block, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                    docs.append({"source": fname, "type": kind, "text": piece})
    return docs


if __name__ == "__main__":
    docs = load_documents()
    print(f"تعداد قطعه‌ها: {len(docs)}")
    for d in docs[:3]:
        print("-", d["source"], "|", d["type"], "|", len(d["text"]), "char")
