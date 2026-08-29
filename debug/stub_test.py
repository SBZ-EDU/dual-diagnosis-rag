from pathlib import Path
"""Stub out the sentence-transformers model with deterministic hash vectors so we can
test the full RAG pipeline (data loading, chunking, store, retriever) without torch."""
import sys, types, hashlib
import numpy as np

# --- fake sentence_transformers module ---
st = types.ModuleType("sentence_transformers")
class FakeModel:
    def __init__(self, name, device=None):
        self.name = name
    def encode(self, texts, **kw):
        out = np.zeros((len(texts), 384), dtype=np.float32)
        for i, t in enumerate(texts):
            h = hashlib.sha256(t.encode("utf-8")).digest()
            seed = int.from_bytes(h[:4], "little")
            rng = np.random.default_rng(seed)
            v = rng.standard_normal(384).astype(np.float32)
            out[i] = v / (np.linalg.norm(v) + 1e-9)
        return out
st.SentenceTransformer = FakeModel
sys.modules["sentence_transformers"] = st

sys.path.insert(0, os.environ.get("RAG_ROOT", str(Path(__file__).resolve().parents[2]) + "/dual-diagnosis-rag"))
import os
os.chdir(os.environ.get("RAG_ROOT", str(Path(__file__).resolve().parents[2]) + "/dual-diagnosis-rag"))

import json
from rag import data

docs = data.load_documents()
print("total chunks:", len(docs))
from collections import Counter
print("by type:", dict(Counter(d["type"] for d in docs)))

# show the pollution: which sources produce junk?
print("\n--- chunks from REPORT files (raw JSON got indexed as knowledge) ---")
for d in docs:
    if d["source"] in ("article_validation_report.json", "extended_corpora_report.json",
                       "open_access_pdf_report.json"):
        print(f"[{d['type']}] {d['source']}: {d['text'][:90]!r}")
        break
report_chunks = [d for d in docs if "report" in d["source"]]
print("report-file chunks:", len(report_chunks))

print("\n--- manifest chunks (bibliography entries with no abstract) ---")
man = [d for d in docs if d["source"] == "open_access_pdf_manifest.jsonl"]
print("manifest chunks:", len(man))
if man:
    print("example:", repr(man[0]["text"][:120]))

print("\n--- empty/near-empty chunks ---")
emptyish = [d for d in docs if len(d["text"].strip()) < 40]
print(len(emptyish), "chunks < 40 chars")
for d in emptyish[:5]:
    print("  ", d["source"], "|", repr(d["text"][:60]))

print("\n--- guidelines chunks (no abstract key in records) ---")
gl = [d for d in docs if d["type"] == "guideline"]
print("guideline chunks:", len(gl))
for d in gl[:3]:
    print("  ", repr(d["text"][:100]))
