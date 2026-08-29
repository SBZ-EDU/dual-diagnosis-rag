"""ساخت فایل seed مقالات برای D1 کلودفلر از پیکره‌های محلی، با فیلتر موضوعی.

پیش از این، مقالات غیرمرتبط (آمار سرطان، راهنمای قلبی ESC، پوکی استخوان و…)
نیز وارد D1 می‌شدند و به‌عنوان «شواهد» به پاسخ‌های /api/chat تزریق می‌شدند.
این اسکریپت فقط مقالات مرتبط با حوزه‌ی تشخیص دوگانه را نگه می‌دارد.

استفاده:
    python -m scripts.build_d1_seed            # خروجی: cloudflare/seed_extended_papers.sql
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPORA = [
    ("international", ROOT / "data/articles/international_100.jsonl"),
    ("iran_affiliated", ROOT / "data/articles/iran_affiliated_100.jsonl"),
]
OUT = ROOT / "cloudflare/seed_extended_papers.sql"

# عبارات قوی: یک مورد در عنوان کافی است؛ در چکیده ۲ امتیاز
STRONG = [
    "psychosis", "psychotic", "schizophrenia", "schizoaffective", "clozapine",
    "antipsychotic", "substance use", "substance-related", "substance abuse",
    "substance misuse", "substance use disorder", "use disorder", "addiction",
    "addictive", "opioid", "opiate", "heroin", "methadone", "buprenorphine",
    "naltrexone", "naloxone", "cannabis", "marijuana", "amphetamine",
    "methamphetamine", "cocaine", "crack", "dual diagnosis", "borderline personality",
    "drug use", "drug abuse", "drug dependence", "drug-related", "drug addiction",
    "drug consumption", "consumption site", "consumption room", "supervised consumption",
    "people who inject", "people who use drug", "needle", "syringe",
    "alcohol use", "alcohol dependence", "alcohol-related", "smoking cessation",
    "nicotine dependence", "injecting drug", "intravenous drug",
]
# عبارات ضعیف: هر مورد ۱ امتیاز
WEAK = [
    "mental health", "mental disorder", "mental illness", "psychiatric",
    "suicide", "suicidal", "self-harm", "stigma", "relapse", "abstinence",
    "withdrawal", "harm reduction", "overdose", "intoxication", "craving",
    "prison", "neuroinflammation", "hiv",
]


def relevance(title: str, abstract: str) -> tuple[int, bool]:
    """(امتیاز، وجود عبارت قوی در عنوان)"""
    text = f"{title}\n{abstract}".lower()
    score = sum(1 for t in WEAK if t in text)
    score += 2 * sum(1 for t in STRONG if t in text)
    strong_in_title = any(t in title.lower() for t in STRONG)
    return score, strong_in_title


def is_relevant(title: str, abstract: str) -> bool:
    score, strong_in_title = relevance(title, abstract)
    if strong_in_title:
        return True
    # اگر چکیده خالی است، فقط عنوان ملاک است و آستانه پایین‌تر می‌آید
    threshold = 1 if not abstract.strip() else 2
    return score >= threshold


def sql_escape(v) -> str:
    if v is None:
        return "''"
    return "'" + str(v).replace("'", "''") + "'"


def main() -> int:
    kept, dropped = [], []
    seen = set()
    for corpus, path in CORPORA:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("openalex_id") in seen:
                continue
            title = r.get("title") or ""
            abstract = r.get("abstract") or ""
            if is_relevant(title, abstract):
                seen.add(r["openalex_id"])
                kept.append(r)
            else:
                dropped.append(title)

    lines = ["-- ساخته‌شده با scripts/build_d1_seed.py (فیلتر موضوعی تشخیص دوگانه)",
             "-- مقالات غیرمرتبط حذف شده‌اند تا به‌عنوان شواهد بالینی تزریق نشوند.",
             "DELETE FROM research_papers;"]
    for r in kept:
        vals = [
            r.get("openalex_id"), r.get("doi"), r.get("title"), r.get("abstract"),
            r.get("year"), r.get("date"), r.get("language"), r.get("journal"),
            r.get("url"), 1 if r.get("open_access") else 0, r.get("corpus"),
            1 if r.get("iran_affiliated") else 0,
            json.dumps(r.get("treatment_tags") or [], ensure_ascii=False),
            r.get("type"), r.get("cited_by_count", 0), r.get("source", "OpenAlex"),
        ]
        # اعداد NULL-پذیر
        out = []
        for v in vals:
            if v is None:
                out.append("NULL")
            elif isinstance(v, (int, float)):
                out.append(str(v))
            else:
                out.append(sql_escape(v))
        lines.append("INSERT OR REPLACE INTO research_papers VALUES(" + ",".join(out) + ");")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"kept: {len(kept)} | dropped: {len(dropped)} -> {OUT}")
    print("\ndropped (غیرمرتبط):")
    for t in dropped:
        print("  -", t[:80])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
