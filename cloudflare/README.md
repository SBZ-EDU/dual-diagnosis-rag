# Cloudflare deployment
Separate Worker + D1 deployment. Existing Workers/databases are not modified.

```bash
npx wrangler d1 execute dual-diagnosis-rag-db --remote --file schema.sql
npx wrangler secret put HF_TOKEN
npx wrangler secret put PATIENT_SALT
npx wrangler deploy
```

The UI exposes `/api/risk` backed by D1 and `/api/chat` backed by Hugging Face. Never store direct identifiers or medical names.

## 🔎 جست‌وجوی معنایی (Vectorize + bge-m3) — راه‌اندازی

ورکر برای بازیابی معنایی آماده است: سؤال با `@cf/baai/bge-m3` (چندزبانه) بردار می‌شود،
مشابه‌ترین تکه‌های پیکره از Vectorize می‌آیند و به زمینه‌ی پاسخ اضافه می‌شوند
(در کنار بازیابی کلیدواژه‌ای D1). اگر بایندینگ/ایندکس نباشد، بی‌صدا غیرفعال است.

یک‌بار برای راه‌اندازی:

```bash
npx wrangler vectorize create ddx-semantic --dimensions 1024 --metric cosine
npx wrangler secret put ADMIN_TOKEN     # یک کلید مخفی دلخواه
npx wrangler deploy
python scripts/embed_corpus.py --url https://dual-diagnosis-clinical-hub.elasa2next.workers.dev --key <ADMIN_TOKEN>
```

- اسکریپت قبل از تعبیه، ابعاد بردار را می‌سنجد (باید ۱۰۲۴ باشد — bge-m3).
- هر اجرا idempotent است (شناسه‌های c0..c1004 بازنویسی می‌شوند).
- متن تکه‌ها در جدول `chunks` پایگاه D1 ذخیره می‌شود؛ بردارها فقط source/type دارند.
- بررسی: `GET /api/admin/embed` (با هدر Bearer) وضعیت ایندکس را می‌دهد.
- سهمیه‌ی رایگان Vectorize: ۵ میلیون بعد ذخیره (پیکره‌ی ما ~۱ میلیون بعد) و ۳۰ میلیون
  بعد پرس‌وجو در ماه (~۵,۸۰۰ پرس‌وجوی معنایی در ماه با topK=5).
