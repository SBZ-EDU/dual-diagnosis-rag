"""ساخت/بازسازی ایندکس برداری از پایگاه دانش.

استفاده:
    python -m scripts.build_index
"""
from __future__ import annotations
import time
import rag.data as data
from rag import embeddings, store


def main():
    t0 = time.time()
    print("۱) بارگذاری اسناد...")
    docs = data.load_documents()
    print(f"   → {len(docs)} قطعه")

    if not docs:
        print("هیچ سندی پیدا نشد. ابتدا data/protocol.md یا فایل‌ها را اضافه کنید.")
        return

    print("۲) امبدینگ قطعه‌ها (بارگذاری مدل، ممکن است کمی طول بکشد)...")
    texts = [d["text"] for d in docs]
    vectors = embeddings.embed(texts)
    print(f"   → شکل بردارها: {vectors.shape}")

    print("۳) ذخیره‌ی ایندکس...")
    store.save(docs, vectors)
    print(f"   ✓ ذخیره شد در index/  ({time.time()-t0:.1f}s)")
    print("\nنمونه‌ی جست‌وجو:")
    from rag import retriever
    for q in ["کلوزاپین چه زمانی؟", "مدل دوسویه چیست؟", "هزینه سطح ۱"]:
        res = retriever.retrieve(q, top_k=1)
        if res:
            print(f"  «{q}» → {res[0]['source']} (score={res[0]['score']:.3f})")


if __name__ == "__main__":
    main()
