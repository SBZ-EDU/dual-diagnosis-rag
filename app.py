"""
دستیار بالینی پروتکل تشخیص دوگانه — اپ Gradio
اسپیس هاشینگ‌فیس. رابط چت + API قابل صدا زدن + جمع‌آوری بازخورد.
اجرا: python app.py  (یا به‌صورت Space روی هاشینگ‌فیس بالا می‌آید)
"""
from __future__ import annotations
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

import config
from rag import retriever, pipeline, store

# ---------- آماده‌سازی ایندکس ----------
def ensure_index():
    if store.exists():
        log.info("ایندکس آماده پیدا شد.")
        return
    log.info("ایندکس موجود نیست؛ در حال ساخت...")
    from scripts import build_index
    build_index.main()


ensure_index()


# ---------- تابع اصلی (هم API و هم رابط چت) ----------
def answer(question: str):
    """سؤال بالینی را پاسخ می‌دهد. این تابع به‌صورت API هم در دسترس است.

    Args:
        question: سؤال کاربر به فارسی.
    Returns:
        (پاسخ، منابع، متادیتا)
    """
    question = (question or "").strip()
    if not question:
        return "لطفاً سؤال خود را بنویسید.", "", {}
    res = pipeline.answer(question)
    src_lines = "\n".join(f"- {s['source']} (نوع: {s['type']}، شباهت: {s['score']})"
                          for s in res["sources"])
    meta = {
        "method": res["method"],
        "num_sources": len(res["sources"]),
        "latency": res["latency"],
    }
    return res["answer"], src_lines, meta


def save_feedback(question: str, answer_text: str, rating: int, comment: str):
    path = pipeline.add_feedback(question or "", answer_text or "", rating, comment or "")
    return f"✅ بازخورد ذخیره شد (فایل: {os.path.basename(path)}). از شما ممنونیم!"


# ---------- رابط کاربری ----------
import gradio as gr

CSS = """
.gradio-container {max-width: 920px !important; font-family: 'Vazirmatn', Tahoma, sans-serif;}
.title {text-align:center;}
.source-box {background:#ecf6f6; border:1px solid #d8e6e6; border-radius:10px; padding:10px;}
"""

with gr.Blocks(title="دستیار پروتکل تشخیص دوگانه", css=CSS, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# ⚕️ دستیار بالینی پروتکل تشخیص دوگانه\n"
        "سایکوز / اسکیزوفرنی + اختلال مصرف مواد + BPD ± ADHD — مبتنی بر شواهد علمی "
        "NICE · APA · WFSBP.\n\n"
        "⚠️ این ابزار جایگزین مشاوره پزشک نیست؛ تصمیم نهایی درمان با پزشک معالج است.",
        elem_classes=["title"])

    with gr.Tab("💬 پرسش و پاسخ"):
        q_in = gr.Textbox(label="سؤال خود را بنویسید", lines=2,
                          placeholder="مثلاً: کلوزاپین چه زمانی تجویز می‌شود؟")
        with gr.Row():
            btn = gr.Button("🩺 پاسخ بده", variant="primary")
        ans_out = gr.Markdown(label="پاسخ")
        src_out = gr.Markdown(label="منابع بازیابی‌شده", visible=True)
        meta_out = gr.JSON(label="متادیتا (روش/تأخیر)")
        btn.click(answer, inputs=q_in, outputs=[ans_out, src_out, meta_out])
        q_in.submit(answer, inputs=q_in, outputs=[ans_out, src_out, meta_out])

        gr.Markdown("#### 📝 ثبت بازخورد (برای آموزش بهتر مدل)")
        with gr.Row():
            rating = gr.Slider(1, 5, value=4, step=1, label="امتیاز پاسخ")
            comment = gr.Textbox(label="توضیح", lines=1)
        fb_btn = gr.Button("ثبت بازخورد")
        fb_out = gr.Markdown()
        fb_btn.click(save_feedback, inputs=[q_in, ans_out, rating, comment], outputs=fb_out)

    with gr.Tab("📚 درباره پایگاه دانش"):
        gr.Markdown(
            "این سیستم از روی **پروتکل درمان تشخیص دوگانه**، **مقالات علمی**، "
            "**سابقه بیمار** و **بازخورد کاربران** پاسخ می‌سازد.\n\n"
            "- فایل‌های مقاله را در `data/articles/` \n"
            "- سابقه بیمار را در `data/patient_history/` \n"
            "- بازخوردها در `data/feedback/` قرار دهید و سپس ایندکس را بازسازی کنید.\n\n"
            "مدل امبدینگ: چندزبانه (MiniLM). مدل مولد: سبک روی CPU رایگان. "
            "اگر مدل مولد در دسترس نباشد، سیستم به‌صورت استخراجی از متن مرجع پاسخ می‌دهد."
        )

    with gr.Tab("🔌 API"):
        gr.Markdown(
            "### نحوه‌ی استفاده از API\n"
            "این اپ به‌صورت خودکار یک REST API ارائه می‌دهد. مثال پایتون:\n"
            "```python\n"
            "from gradio_client import Client\n"
            "c = Client(\"<این-اسپیس>\")\n"
            "ans, sources, meta = c.predict(question=\"کلوزاپین چه زمانی؟\", api_name=\"/answer\")\n"
            "print(ans)\n"
            "```\n"
            "همچنین می‌توانید به‌صورت POST به `/call/answer` درخواست بزنید."
        )


# مونتاژ روی ۰.۰.۰.۰ برای پیش‌نمایش زنده
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
