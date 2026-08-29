#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تعبیه‌ی پیکره‌ی دانش (index/chunks.json) در Vectorize کلودفلر از طریق ورکر.

پیش‌نیازها:
  1) ایندکس ساخته شده باشد:
     npx wrangler vectorize create ddx-semantic --dimensions 1024 --metric cosine
  2) ورکر با بایندینگ VEC دیپلوی شده و راز ADMIN_TOKEN تنظیم شده باشد:
     npx wrangler secret put ADMIN_TOKEN && npx wrangler deploy
  3) سپس:  python scripts/embed_corpus.py --url https://dual-diagnosis-clinical-hub.elasa2next.workers.dev

اجرا با احتیاط: هر اجرا، همین ۱۰۰۵ تکه را با همان شناسه‌ها بازنویسی می‌کند (idempotent).
گزینه‌ها:
  --key     مقدار ADMIN_TOKEN (یا متغیر محیطی ADMIN_TOKEN)
  --batch   اندازه‌ی دسته (پیش‌فرض ۴۰)
  --start/--end  بازه‌ی تکه‌ها (برای ادامه‌ی اجرای ناتمام)
  --reset   پاک‌کردن جدول chunks قبل از شروع
  --dry-run فقط نمایش دسته‌ها بدون ارسال
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

DEFAULT_URL = "https://dual-diagnosis-clinical-hub.elasa2next.workers.dev"


def post(url: str, key: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url.rstrip("/") + "/api/admin/embed",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"content-type": "application/json",
                 "authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main() -> None:
    ap = argparse.ArgumentParser(description="Embed corpus into Cloudflare Vectorize via the worker")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--key", default=os.environ.get("ADMIN_TOKEN", ""))
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chunks = json.load(open(os.path.join(root, "index", "chunks.json"), encoding="utf-8"))
    end = len(chunks) if a.end is None else min(a.end, len(chunks))
    todo = list(range(a.start, end))
    print(f"chunks: {len(chunks)} total | embedding [{a.start}:{end}] | batch={a.batch} | url={a.url}")

    if a.dry_run:
        for s in range(0, len(todo), a.batch):
            part = todo[s:s + a.batch]
            print(f"  dry-run batch: chunks {part[0]}..{part[-1]} ({len(part)} items)")
        print("dry-run OK — nothing sent")
        return

    if not a.key:
        sys.exit("ERROR: --key or ADMIN_TOKEN env var required")

    # ۱) بررسی ابعاد بردار قبل از هر کاری (باید با ابعاد ایندکس یکسان باشد)
    probe = post(a.url, a.key, {"probe": "آزمون ابعاد بردار فارسی"})
    dims = probe.get("dims")
    print(f"probe → dims={dims}")
    if dims != 1024:
        print(f"⚠️  dims={dims} but index was created for 1024 — recreate the index with --dimensions {dims} and retry")
        sys.exit(1)

    # ۲) تعبیه‌ی دسته‌ای
    done = 0
    for s in range(0, len(todo), a.batch):
        part = todo[s:s + a.batch]
        payload = {"items": [
            {"i": i, "text": chunks[i].get("text", ""),
             "source": chunks[i].get("source", "?"), "type": chunks[i].get("type", "text")}
            for i in part]}
        if a.reset and s == 0:
            payload["reset"] = True
        r = post(a.url, a.key, payload)
        if not r.get("ok"):
            sys.exit(f"ERROR at chunks {part[0]}..{part[-1]}: {r}")
        done += r.get("upserted", 0)
        print(f"  batch {part[0]}..{part[-1]} → upserted {r.get('upserted')} (dims {r.get('dims')})")

    print(f"DONE ✅ {done}/{len(todo)} chunks embedded. Test: POST /api/chat with a Persian question and check `semantic` in the response.")


if __name__ == "__main__":
    main()
