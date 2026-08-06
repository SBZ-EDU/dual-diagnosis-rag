"""افزودن یک سند جدید به پایگاه دانش و بازسازی ایندکس.

استفاده:
    python -m scripts.ingest --kind articles --file my_paper.md
    python -m scripts.ingest --kind patient_history --file patient_001.json --text "..."
    kind یکی از: articles | patient_history | feedback
"""
from __future__ import annotations
import argparse
import os
import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True,
                    choices=["articles", "patient_history", "feedback"])
    ap.add_argument("--file", help="مسیر فایل برای کپی به پوشه‌ی منبع")
    ap.add_argument("--name", help="نام فایل مقصد (پیش‌فرض: نام فایل اصلی)")
    ap.add_argument("--text", help="متن مستقیم به‌جای فایل")
    args = ap.parse_args()

    dest_dir = config.SOURCES[args.kind]
    os.makedirs(dest_dir, exist_ok=True)

    if args.text is not None:
        name = args.name or "manual_note.md"
        path = os.path.join(dest_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(args.text)
        print(f"✓ متن ذخیره شد: {path}")
    elif args.file:
        name = args.name or os.path.basename(args.file)
        path = os.path.join(dest_dir, name)
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ فایل کپی شد: {path}")
    else:
        ap.error("یا --file یا --text را بدهید.")

    print("\nبازسازی ایندکس...")
    from scripts import build_index
    build_index.main()


if __name__ == "__main__":
    main()
