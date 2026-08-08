---
title: دستیار پروتکل تشخیص دوگانه
emoji: ⚕️
colorFrom: teal
colorTo: blue
sdk: gradio
sdk_version: "4.44.1"
app_file: app.py
pinned: false
tags:
  - rag
  - psychology
  - mental-health
  - persian
  - llama
  - wandb
language:
  - fa
---

# ⚕️ دستیار بالینی پروتکل تشخیص دوگانه (RAG)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SBZ-EDU/dual-diagnosis-rag/blob/master/notebooks/Dual_Diagnosis_RAG_Colab.ipynb)

**اجرای یک‌کلیکی Colab:** دریافت دیتاست‌ها، دانلود خودکار PDFهای Open Access با سقف حجم، استخراج متن، آپلود PDF/کتاب مجاز، بازسازی و آزمون RAG، Fine-tune اختیاری، ثبت W&B و تحویل ZIP خروجی.

> سایکوز / اسکیزوفرنی + اختلال مصرف مواد + BPD ± ADHD
> مبتنی بر شواهد علمی NICE · APA · WFSBP

یک سیستم **پرسش‌وپاسخ مبتنی بر بازیابی (RAG)** با هوش مصنوعی که از روی **پروتکل درمان تشخیص دوگانه**، **مقالات علمی**، **سابقه بیمار** و **بازخورد کاربران** پاسخ می‌سازد.

---

## ✨ امکانات

- 💬 **رابط چت فارسی** + 🔌 **REST API** قابل صدا زدن (Gradio Client یا HTTP)
- 🧠 **مدل اوپن‌سورس سبک** (پیش‌فرض: Qwen2.5-0.5B-Instruct روی CPU رایگان) — قابل تعویض به Llama یا هر مدل دیگر
- 📚 **RAG چندمنبعی**: پروتکل + مقالات + سابقه بیمار + بازخورد
- 🔍 **بازیابی معنایی** با امبدینگ چندزبانه (شامل فارسی)
- 🪙 **اتصال به W&B (wandb)** برای لاگ کوئری‌ها، منابع و تأخیر + اسکریپت آموزش
- 🛡️ **حالت افت‌گرایانه**: اگر مدل مولد بارگذاری نشد، از متن مرجع استخراج می‌کند (همیشه کار می‌کند)
- 📝 جمع‌آوری **بازخورد کاربران** برای آموزش آینده
- 📈 **پایش روزانه/هفتگی خطر** با امتیاز شفاف، سطح اقدام و API مستقل `/risk`
- 📰 **رصد هفتگی PubMed** با GitHub Actions و ذخیره مقالات جدید برای بازبینی و ورود به RAG

> سامانه فقط تغییر شواهد و سطح نیاز به بازبینی را هشدار می‌دهد؛ تغییر خودکار دارو/درمان ممنوع است و تأیید پزشک لازم است.

---

## 🚀 اجرا

```bash
pip install -r requirements.txt

# ساخت ایندکس برداری از پایگاه دانش
python -m scripts.build_index

# اجرای اپ
python app.py            # http://localhost:7860
```

روی **هاشینگ‌فیس اسپیس** به‌صورت خودکار بالا می‌آید.

---

## 🧩 پیکربندی (متغیرهای محیطی)

| متغیر | پیش‌فرض | توضیح |
|------|---------|-------|
| `EMBED_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | مدل امبدینگ |
| `GEN_MODEL` | `Qwen/Qwen2.5-0.5B-Instruct` | مدل مولد (برای لاما: `meta-llama/Llama-3.2-1B-Instruct` و غیره) |
| `USE_GENERATOR` | `1` | `0` = فقط بازیابی/استخراج |
| `TOP_K` | `5` | تعداد قطعه‌های بازیابی‌شده |
| `WANDB_API_KEY` | — | در صورت تنظیم، لاگ‌گیری فعال می‌شود |
| `WANDB_PROJECT` | `dual-diagnosis-rag` | نام پروژه‌ی W&B |
| `WANDB_ENTITY` | `elasa2next-sosa-` | موجودیت W&B |

---

## 📂 افزودن منبع جدید

```bash
# افزودن یک مقاله و بازسازی ایندکس
python -m scripts.ingest --kind articles --file paper.md

# افزودن متن مستقیم
python -m scripts.ingest --kind patient_history --name p001.md --text "..."
```

فقط کافی است فایل‌ها را در پوشه‌ی مربوطه بگذارید:
- `data/articles/` — مقالات علمی
- `data/patient_history/` — سابقه بیمار
- `data/feedback/` — بازخورد کاربران (خودکار از رابط جمع می‌شود)

سپس `python -m scripts.build_index` را اجرا کنید.

---

## 🎓 آموزش/Fine-tune (با W&B)

```bash
python -m scripts.train --model Qwen/Qwen2.5-0.5B-Instruct --epochs 3
```

داده‌ی آموزشی در `data/instruction_pairs.jsonl`. این اسکریپت از **LoRA (peft)** استفاده می‌کند و به **GPU** نیاز دارد (روی CPU بسیار کند است).

---

## 🗂️ ساختار

```
.
├── app.py                      # اپ Gradio (رابط + API)
├── config.py                   # تنظیمات
├── requirements.txt
├── rag/                        # موتور RAG
│   ├── data.py                 # بارگذاری و قطعه‌بندی
│   ├── embeddings.py           # امبدینگ چندزبانه
│   ├── store.py                # ذخیره/بازیابی برداری
│   ├── retriever.py            # بازیابی معنایی
│   ├── generator.py            # مدل مولد + حالت استخراجی
│   └── pipeline.py             # هماهنگی + لاگ W&B
├── data/
│   ├── protocol.md             # پایگاه دانش اصلی
│   ├── instruction_pairs.jsonl # داده‌ی آموزشی
│   ├── articles/  patient_history/  feedback/
├── scripts/
│   ├── build_index.py          # ساخت ایندکس
│   ├── ingest.py               # افزودن سند
│   └── train.py                # fine-tune با LoRA + W&B
```

---

## 🧪 دموی زنده و تست RAG نقش‌محور

- Cloudflare UI: https://dual-diagnosis-clinical-hub.elasa2next.workers.dev
- API: `POST /api/chat` با بدنه `{"role":"patient|family|doctor|admin","question":"..."}`
- در رابط، از بخش **دستیار علمی** نقش مخاطب را انتخاب کنید.

> مخزن Hugging Face صفحه میزبانی کد/مدل است؛ رابط عمومی فعال روی Cloudflare میزبانی می‌شود.

## 📊 پایش W&B

داشبورد اجرای RAG، تأخیر و چرخه‌های به‌روزرسانی داده:
https://wandb.ai/elasa2next-sosa-/dual-diagnosis-rag

## ⚠️ سلب مسئولیت

این ابزار صرفاً **آموزشی** است و جایگزین مشاوره پزشک نیست. تصمیم نهایی درمان همیشه با پزشک معالج است.
