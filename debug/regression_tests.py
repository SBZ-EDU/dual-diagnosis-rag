from pathlib import Path
"""Regression tests for the fixed dual-diagnosis-rag code (run from repo root)."""
import sys, os, json, time
sys.path.insert(0, os.environ.get("RAG_ROOT", str(Path(__file__).resolve().parents[2]) + "/dual-diagnosis-rag"))
os.chdir(os.environ.get("RAG_ROOT", str(Path(__file__).resolve().parents[2]) + "/dual-diagnosis-rag"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ["USE_GENERATOR"] = "0"

from rag import data, store
from monitoring.risk_engine import assess

failures = []
def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not cond: failures.append(name)

# ---------- 1) data loading ----------
docs = data.load_documents()
check("documents load", len(docs) > 500, f"{len(docs)} chunks")
check("no report/manifest junk", not any("report" in d["source"] or "manifest" in d["source"] for d in docs))
check("no tiny chunks", all(len(d["text"].strip()) >= 40 for d in docs))
check("guidelines present", any(d["type"] == "guideline" for d in docs))
check("articles present", sum(1 for d in docs if d["type"] == "article") > 900)

# ---------- 2) header merging ----------
blocks = data._split_markdown_by_headers("# A\nbody A\n## B\n## C\nbody C")
check("header-only chunk merged", all(not b.startswith("## B\n") or len(b) > 10 for b in blocks), str(blocks))

# ---------- 3) risk engine ----------
r = assess({"psychosis": 0, "suicide": 0, "violence": 0, "withdrawal": 0,
            "substance_use": 0, "sleep_loss": 0, "nonadherence": 0})
check("risk: all-zero → low", r["level"] == "پایین" and r["score"] == 0)
r = assess({"suicide": 4})
check("risk: suicide=4 → critical", r["level"] == "بحرانی")
r = assess({"withdrawal": 4})
check("risk: withdrawal=4 → critical", r["level"] == "بحرانی")
r = assess({"flags": ["suicidal_plan"]})
check("risk: red flag → critical", r["level"] == "بحرانی" and r["red_flags"] == ["suicidal_plan"])
r = assess({"psychosis": 9, "suicide": -3})
check("risk: input clamping", r["inputs"]["psychosis"] == 4 and r["inputs"]["suicide"] == 0)
r = assess({k: 4 for k in ["psychosis","suicide","violence","withdrawal","substance_use","sleep_loss","nonadherence"]})
check("risk: max score = 76", r["score"] == 76, f"score={r['score']}")

# ---------- 4) store caching ----------
c1, v1 = store.load()
c2, v2 = store.load()
check("store: cached object identity", c1 is c2 and v1 is v2)
check("store: manifest matches after build", store.manifest_matches())

# mtime invalidation: touch a data file → manifest should mismatch
p = "data/protocol.md"
st = os.stat(p)
os.utime(p, (st.st_atime, st.st_mtime + 5))
check("store: stale detection on data change", not store.manifest_matches())
os.utime(p, (st.st_atime, st.st_mtime))  # restore
check("store: manifest matches again", store.manifest_matches())

# search edge cases
import numpy as np
empty = np.zeros((0, 384), dtype=np.float32)
check("store: search on empty index", store.search(np.ones(384, dtype=np.float32), empty, 5) == [])
vecs = np.eye(5, 384, dtype=np.float32)
check("store: top-k ordering", store.search(vecs[0], vecs, 2) == [0, 1])

# ---------- 5) retrieval with real model ----------
from rag import retriever
res = retriever.retrieve("کلوزاپین چه زمانی تجویز می‌شود؟", top_k=3)
check("retrieval returns sources", len(res) == 3 and all("score" in s for s in res))
top = res[0]
check("retrieval relevance (clozapine)", "clozapine" in (res[0]["text"] + res[1]["text"]).lower() or "کلوزاپین" in (res[0]["text"] + res[1]["text"]),
      f"top: {top['source']} ({top['score']:.3f})")
res2 = retriever.retrieve("متادون برای وابستگی به مواد افیونی", top_k=8)
check("retrieval finds methadone guideline/article", any("متادون" in s["text"].lower() or "methadone" in s["text"].lower() for s in res2))

# ---------- 6) feedback format ----------
from rag import pipeline
path = pipeline.add_feedback("تست؟", "پاسخ تست", 5, "خوب بود")
rec = json.load(open(path))
check("feedback tz-aware timestamp", rec["ts"].endswith("+00:00") and "Z" not in rec["ts"][-6:], rec["ts"])
os.remove(path)

print()
print("FAILED:" if failures else "ALL TESTS PASSED ✅", failures or "")
sys.exit(1 if failures else 0)
