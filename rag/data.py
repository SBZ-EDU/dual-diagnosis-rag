"""شکستن متن پایگاه دانش به قطعه‌های قابل‌بازیابی و بارگذاری اسناد اضافه."""
from __future__ import annotations
import os
import json
import re
from typing import List, Dict
import config

# فایل‌های متادیتا/گزارش که نباید به‌عنوان دانش وارد ایندکس شوند
# (قبلاً JSON خامِ این فایل‌ها به‌عنوان «مقاله» ایندکس می‌شد و بازیابی را خراب می‌کرد)
EXCLUDE_FILES = {
    "article_validation_report.json",
    "extended_corpora_report.json",
    "open_access_pdf_report.json",
    "open_access_pdf_manifest.jsonl",
}
_EXCLUDE_PATTERN = re.compile(r"(_report\.json|_manifest\.jsonl)$")

# حداقل طول متن معتبر برای یک قطعه (کاراکتر)
MIN_CHUNK_LEN = 40


def _is_excluded(fname: str) -> bool:
    return fname in EXCLUDE_FILES or bool(_EXCLUDE_PATTERN.search(fname))


def _split_markdown_by_headers(text: str) -> List[str]:
    """متن مارک‌داون را بر اساس سرتیترها به قطعه‌ی معنادار می‌شکند.

    سرتیترهایی که بدنه‌ی خالی دارند به‌عنوان قطعه‌ی مسترد ثبت نمی‌شوند؛
    به‌عنوان پیشوندِ زمینه به قطعه‌ی بعدی می‌چسبند.
    """
    lines = text.splitlines()
    chunks: List[str] = []
    buffer: List[str] = []
    header_prefix: List[str] = []

    def flush():
        nonlocal header_prefix
        if buffer:
            block = "\n".join(header_prefix + buffer).strip()
            if block:
                chunks.append(block)
            buffer.clear()
            header_prefix = []

    for line in lines:
        if re.match(r"^#{1,4}\s", line):
            # اگر از آخرین سرتیتر متن واقعی نیامده باشد، سرتیترها انباشته می‌شوند
            if buffer:
                flush()
            header_prefix.append(line)
        else:
            buffer.append(line)
    flush()
    # اگر در انتها فقط سرتیتر ماند، به قطعه‌ی قبلی بچسبان
    if header_prefix and chunks:
        chunks[-1] = (chunks[-1] + "\n" + "\n".join(header_prefix)).strip()
    elif header_prefix:
        chunks.append("\n".join(header_prefix))
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


def _record_text(rec: Dict) -> str:
    """رکورد JSON/JSONL را به متن ساخت‌یافته برای RAG تبدیل می‌کند.

    توجه: URL عمداً در متن نیامده — توکن‌های زیاد لینک، بردار امبدینگ را رقیق
    می‌کند و شباهت معنایی را تا نصف کاهش می‌دهد. URL در فیلد «source» حفظ می‌شود.
    """
    parts = []
    title = rec.get("title")
    if title:
        parts.append(str(title))
    body = rec.get("abstract") or rec.get("text") or rec.get("summary")
    if body:
        parts.append(str(body))
    meta_bits = []
    for key in ("journal", "organization", "published", "year", "date"):
        val = rec.get(key)
        if val:
            meta_bits.append(str(val))
    if meta_bits:
        parts.append(" | ".join(meta_bits))
    return "\n".join(parts)


def _feedback_text(rec: Dict) -> str:
    """بازخورد کاربر را به متن خوانا تبدیل می‌کند (به‌جای JSON خام)."""
    parts = ["بازخورد کاربر"]
    if rec.get("question"):
        parts.append(f"سؤال: {rec['question']}")
    if rec.get("answer"):
        parts.append(f"پاسخ: {rec['answer']}")
    if rec.get("rating") is not None:
        parts.append(f"امتیاز: {rec['rating']} از ۵")
    if rec.get("comment"):
        parts.append(f"توضیح: {rec['comment']}")
    return "\n".join(parts)


def _record_source(rec: Dict, fname: str) -> str:
    return rec.get("url") or rec.get("doi") or rec.get("id") or fname


def load_documents() -> List[Dict]:
    """همه‌ی منابع (پروتکل + مقالات + سابقه بیمار + بازخورد) را بارگذاری می‌کند."""
    docs: List[Dict] = []

    def add_pieces(text: str, source: str, kind: str):
        for block in _split_markdown_by_headers(text):
            for piece in _chunk_text(block, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                if len(piece.strip()) >= MIN_CHUNK_LEN:
                    docs.append({"source": source, "type": kind, "text": piece})

    # ۱) پروتکل اصلی
    if os.path.exists(config.PROTOCOL_FILE):
        with open(config.PROTOCOL_FILE, "r", encoding="utf-8") as f:
            protocol = f.read()
        for block in _split_markdown_by_headers(protocol):
            for piece in _chunk_text(block, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                if len(piece.strip()) >= MIN_CHUNK_LEN:
                    docs.append({"source": "protocol.md", "type": "protocol", "text": piece})

    # ۲) منابع اضافه از پوشه‌ها
    type_map = {"articles": "article", "guidelines": "guideline",
                "patient_history": "patient", "feedback": "feedback"}
    for folder, kind in type_map.items():
        d = config.SOURCES[folder]
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            path = os.path.join(d, fname)
            if not os.path.isfile(path) or fname.startswith(".") or _is_excluded(fname):
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
                    if kind == "feedback":
                        text = _feedback_text(rec)
                    else:
                        text = _record_text(rec)
                    # رکوردهای فقط-عنوان (مانند فهرست کتاب‌شناسی) ارزش بازیابی ندارند
                    if len(text.strip()) < MIN_CHUNK_LEN:
                        continue
                    add_pieces(text, _record_source(rec, fname), kind)
                continue
            add_pieces(raw, fname, kind)
    return docs


if __name__ == "__main__":
    docs = load_documents()
    print(f"تعداد قطعه‌ها: {len(docs)}")
    for d in docs[:3]:
        print("-", d["source"], "|", d["type"], "|", len(d["text"]), "char")
