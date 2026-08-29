"""
ربات تلگرامِ دستیار بالینی پروتکل تشخیص دوگانه.

از همان خط لوله‌ی RAG پروژه (rag.pipeline) و موتور پایش خطر (monitoring.risk_engine)
استفاده می‌کند؛ پاسخ‌ها همیشه با سلب مسئولیت پزشکی ارسال می‌شوند.

اجرا:
    TELEGRAM_BOT_TOKEN=... python telegram_bot.py
یا قرار دادن توکن در فایل .env (که در گیت نادیده گرفته می‌شود).

نکته‌ی ایمنی: توکن هرگز در کد یا گیت ذخیره نمی‌شود؛ فقط از متغیر محیطی/.env خوانده
می‌شود و محتوای پیام‌های کاربران در لاگ ثبت نمی‌شود.
"""
from __future__ import annotations
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("telegram-bot")

import config

# بررسی توکن پیش از بارگذاری کتابخانه‌های سنگین
if not config.TELEGRAM_BOT_TOKEN:
    raise SystemExit(
        "TELEGRAM_BOT_TOKEN تنظیم نشده است.\n"
        "آن را در فایل .env کنار پروژه بگذارید (الگوی .env.example) یا به‌صورت\n"
        "متغیر محیطی وارد کنید:  TELEGRAM_BOT_TOKEN=123:abc python telegram_bot.py"
    )

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters,
)

from rag import pipeline, store
from monitoring.risk_engine import assess as assess_risk
import telegram_posts

from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

TEHRAN_TZ = ZoneInfo("Asia/Tehran")

DISCLAIMER = "⚠️ این پاسخ از پایگاه دانش علمی استخراج شده و جایگزین مشاوره پزشک نیست؛ تصمیم نهایی درمان با پزشک معالج است."

RISK_FIELDS = [
    ("psychosis", "روان‌پریشی"),
    ("suicide", "خودکشی (افکار/برنامه)"),
    ("violence", "خشونت"),
    ("withdrawal", "علائم ترک ماده"),
    ("substance_use", "مصرف ماده"),
    ("sleep_loss", "کم‌خوابی"),
    ("nonadherence", "عدم پایبندی به درمان"),
]

MAX_LEN = 3800  # سقف ایمن تلگرام ۴۰۹۶ است؛ حاشیه می‌گذاریم

WELCOME = (
    "سلام! 👋\n\n"
    "من دستیار بالینی *پروتکل تشخیص دوگانه* هستم\n"
    "(سایکوز / اسکیزوفرنی + اختلال مصرف مواد + BPD ± ADHD).\n\n"
    "مبتنی بر پروتکل درمان، ۲۰۰+ مقاله علمی و راهنماهای NICE · APA · WFSBP · WHO پاسخ می‌دهم.\n\n"
    "*نحوه‌ی استفاده:*\n"
    "• سؤال بالینی‌تان را همین‌جا بنویسید (فارسی یا انگلیسی)\n"
    "• /risk — پایش خطر روزانه/هفتگی با پرسش‌های مرحله‌ای\n"
    "• /about — درباره‌ی پایگاه دانش\n"
    "• /help — فهرست دستورها\n\n"
    "⚠️ _من جایگزین پزشک نیستم؛ در وضعیت اورژانسی فوراً با خدمات درمانی تماس بگیرید._"
)

HELP_TEXT = (
    "📖 *راهنما*\n\n"
    "• پیام آزاد → پاسخ RAG از پروتکل، مقالات و راهنماها\n"
    "• /ask سؤال → همان پاسخ (مناسب گروه‌ها)\n"
    "• /risk → ارزیابی خطر ۷ شاخصه (۰ تا ۴)\n"
    "• /cancel → لغو ارزیابی در جریان\n"
    "• /about → منابع دانش\n\n"
    "🔒 حریم خصوصی: متن پیام‌های شما ذخیره یا لاگ نمی‌شود؛ ارزیابی خطر بدون نام بیمار است."
)

ABOUT_TEXT = (
    "📚 *درباره‌ی پایگاه دانش*\n\n"
    "• پروتکل درمان تشخیص دوگانه (سند داخلی)\n"
    "• ۲۰۰+ مقاله علمی (OpenAlex/Crossref/PubMed، اعتبارسنجی‌شده)\n"
    "• راهنماهای بالینی: NICE، APA، WFSBP، WHO، UNODC و وزارت بهداشت ایران\n"
    "• بازیابی معنایی چندزبانه با امبدینگ paraphrase-multilingual-MiniLM\n\n"
    "شواهد به‌صورت هفتگی با PubMed به‌روزرسانی می‌شوند."
)

# ---------------- ابزارها ----------------

def split_message(text: str, limit: int = MAX_LEN) -> list[str]:
    """متن را به قطعه‌های ≤ limit کاراکتر، در مرز خط می‌شکند."""
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    cur = ""
    for line in text.split("\n"):
        while len(line) > limit:  # خط خیلی طولانی بدون مرز
            parts.append(line[:limit])
            line = line[limit:]
        if len(cur) + len(line) + 1 > limit:
            parts.append(cur.rstrip("\n"))
            cur = line + "\n"
        else:
            cur += line + "\n"
    if cur.strip():
        parts.append(cur.rstrip("\n"))
    return parts


def format_answer(question: str) -> str:
    """پرس‌وجو را از خط لوله‌ی RAG پاسخ می‌دهد و قالب پیام تلگرام را می‌سازد."""
    res = pipeline.answer(question)
    lines = [res["answer"].rstrip(), ""]
    top = res["sources"][:3]
    if top:
        lines.append("📚 منابع:")
        for i, s in enumerate(top, 1):
            src = s["source"] if len(s["source"]) <= 60 else s["source"][:57] + "…"
            lines.append(f"{i}. {src} (شباهت {s['score']})")
        lines.append("")
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def format_risk_report(result: dict) -> str:
    """خروجی موتور خطر را به پیام خوانا تبدیل می‌کند."""
    inputs = result.get("inputs", {})
    vals = " | ".join(f"{label}: {inputs.get(key, 0)}" for key, label in RISK_FIELDS)
    return (
        f"🩺 *گزارش پایش خطر*\n\n"
        f"امتیاز: *{result['score']} از ۷۶*\n"
        f"سطح: *{result['level']}*\n\n"
        f"📌 اقدام پیشنهادی:\n{result['action']}\n\n"
        f"ثبت‌شده‌ها: {vals}\n\n"
        f"{result['disclaimer']}"
    )


async def send_long(update: Update, text: str, **kw):
    for part in split_message(text):
        await update.effective_message.reply_text(part, **kw)


def throttled(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ضدسیل ساده برای محافظت از CPU؛ برای هر کاربر فاصله‌ی حداقلی الزامی است."""
    now = time.monotonic()
    last = context.user_data.get("_last_ts", 0.0)
    if now - last < config.TELEGRAM_COOLDOWN_S:
        return True
    context.user_data["_last_ts"] = now
    return False


# ---------------- دستورها ----------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(WELCOME, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(ABOUT_TEXT, parse_mode="Markdown")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.pop("risk", None) is not None:
        await update.effective_message.reply_text("ارزیابی خطر لغو شد. ✅")
    else:
        await update.effective_message.reply_text("ارزیابی در جریانی وجود ندارد.")


# ---------------- پرسش و پاسخ RAG ----------------

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    question = (question or "").strip()
    if not question:
        await update.effective_message.reply_text("لطفاً سؤال خود را بنویسید. مثال: /ask کلوزاپین چه زمانی تجویز می‌شود؟")
        return
    if throttled(update.effective_user.id, context):
        await update.effective_message.reply_text("⏳ چند لحظه صبر کنید و دوباره بپرسید.")
        return
    chat = update.effective_chat
    typing = asyncio.create_task(_keep_typing(chat.id, context))
    try:
        # پاسخ‌دهی CPU-محور است؛ در نخ جدا اجرا می‌شود تا event-loop قفل نشود
        text = await asyncio.to_thread(format_answer, question)
        await send_long(update, text)
    except Exception:
        log.exception("خطا در پاسخ‌دهی RAG (user_id=%s)", update.effective_user.id)
        await update.effective_message.reply_text("متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    finally:
        typing.cancel()


async def _keep_typing(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """تا پایان تولید پاسخ، وضعیت «در حال نوشتن…» را زنده نگه می‌دارد."""
    try:
        while True:
            await context.bot.send_chat_action(chat_id, action="typing")
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_question(update, context, update.effective_message.text)


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_question(update, context, " ".join(context.args or []))


# ---------------- پایش خطر (گفت‌وگوی مرحله‌ای) ----------------

def _risk_keyboard(step: int) -> InlineKeyboardMarkup:
    keys = [[InlineKeyboardButton(str(i), callback_data=f"risk:{i}") for i in range(5)]]
    return InlineKeyboardMarkup(keys)


async def cmd_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["risk"] = {"step": 0, "answers": {}}
    await _ask_risk_step(update, context)


async def _ask_risk_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("risk")
    if state is None:
        await update.effective_message.reply_text("برای شروع /risk را بزنید.")
        return
    step = state["step"]
    if step >= len(RISK_FIELDS):
        await _finish_risk(update, context)
        return
    key, label = RISK_FIELDS[step]
    msg = await update.effective_message.reply_text(
        f"🩺 پایش خطر — {step + 1} از {len(RISK_FIELDS)}\n\n"
        f"«{label}» الان چقدر شدت دارد؟\n(۰ = ندارد … ۴ = شدید)",
        reply_markup=_risk_keyboard(step),
    )
    state["qmsg"] = msg.message_id  # فقط دکمه‌های آخرین پرسش معتبرند


async def on_risk_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    state = context.user_data.get("risk")
    if state is None:
        await q.answer("جلسه‌ی ارزیابی منقضی شده است؛ دوباره /risk را بزنید.", show_alert=True)
        return
    if q.message is None or state.get("qmsg") != q.message.message_id:
        await q.answer("این پرسش قدیمی است؛ به آخرین پرسش پاسخ دهید.")
        return
    try:
        value = int(q.data.split(":", 1)[1])
        value = max(0, min(4, value))
    except (ValueError, IndexError):
        return
    await q.answer()
    key, label = RISK_FIELDS[state["step"]]
    state["answers"][key] = value
    state["step"] += 1
    await q.edit_message_text(f"«{label}»: {value} ثبت شد ✅")
    if state["step"] < len(RISK_FIELDS):
        await _ask_risk_step(update, context)
    else:
        await _finish_risk(update, context)


async def _finish_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.pop("risk", None)
    if state is None:
        return
    result = assess_risk(state["answers"])
    # ذخیره‌ی نتیجه در Firestore به این ربات عمومی سپرده نمی‌شود (ملاحظات حریم خصوصی)
    await send_long(update, format_risk_report(result), parse_mode="Markdown")


# ---------------- ارسال خودکار به کانال ----------------

def is_admin(update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id in config.TELEGRAM_ADMIN_IDS)


async def post_to_channel(bot, text: str) -> None:
    """متن را به کانال پیکربندی‌شده می‌فرستد (با احترام به سقف ۴۰۹۶ کاراکتر)."""
    if not config.TELEGRAM_CHANNEL_ID:
        raise RuntimeError("TELEGRAM_CHANNEL_ID تنظیم نشده است.")
    chat_id = config.TELEGRAM_CHANNEL_ID.strip()
    for part in split_message(text):
        await bot.send_message(chat_id=chat_id, text=part)


async def job_daily_tip(context: ContextTypes.DEFAULT_TYPE):
    """پست آموزشی روزانه به کانال."""
    try:
        await post_to_channel(context.bot, telegram_posts.tip_of_day())
        log.info("پست آموزشی روزانه به کانال ارسال شد.")
    except Exception as e:
        log.warning("ارسال پست آموزشی ناموفق: %s", e)


async def job_weekly_digest(context: ContextTypes.DEFAULT_TYPE):
    """بررسی روزانه: فقط دوشنبه‌ها رصد هفتگی شواهد PubMed ارسال می‌کند."""
    if datetime.now(TEHRAN_TZ).weekday() != 0:
        return
    digest = await asyncio.to_thread(telegram_posts.weekly_digest)
    if not digest:
        log.info("رصد هفتگی: مقاله‌ای پیدا/دریافت نشد؛ ارسال نشد.")
        return
    try:
        await post_to_channel(context.bot, digest)
        log.info("رصد هفتگی شواهد به کانال ارسال شد.")
    except Exception as e:
        log.warning("ارسال رصد هفتگی ناموفق: %s", e)


async def cmd_post_tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.effective_message.reply_text("این دستور فقط برای مدیران ربات است.")
        return
    try:
        await post_to_channel(context.bot, telegram_posts.tip_of_day())
        await update.effective_message.reply_text("✅ پست آموزشی امروز به کانال ارسال شد.")
    except Exception as e:
        await update.effective_message.reply_text(f"ارسال ناموفق: {e}")


async def cmd_post_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.effective_message.reply_text("این دستور فقط برای مدیران ربات است.")
        return
    msg = await update.effective_message.reply_text("⏳ در حال دریافت مقالات جدید PubMed...")
    digest = await asyncio.to_thread(telegram_posts.weekly_digest)
    if not digest:
        await msg.edit_text("مقاله‌ای دریافت نشد (خطای شبکه یا بدون نتیجه).")
        return
    try:
        await post_to_channel(context.bot, digest)
        await msg.edit_text("✅ رصد هفتگی به کانال ارسال شد.")
    except Exception as e:
        await msg.edit_text(f"ارسال ناموفق: {e}")


async def cmd_channel_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.effective_message.reply_text("این دستور فقط برای مدیران ربات است.")
        return
    if not config.TELEGRAM_CHANNEL_ID:
        await update.effective_message.reply_text(
            "TELEGRAM_CHANNEL_ID تنظیم نشده است.\n"
            "برای کانال عمومی همان @username را در .env بگذارید؛ برای کانال خصوصی شناسه‌ی "
            "عددی -100... (پس از افزودن ربات به‌عنوان مدیر، شناسه در لاگ ربات ثبت می‌شود)."
        )
        return
    try:
        chat = await context.bot.get_chat(config.TELEGRAM_CHANNEL_ID)
        await update.effective_message.reply_text(
            f"✅ کانال در دسترس است:\nعنوان: {chat.title}\nشناسه: {chat.id}\nنوع: {chat.type}"
        )
    except Exception as e:
        await update.effective_message.reply_text(
            f"❌ دسترسی به کانال برقرار نشد: {e}\n"
            "مطمئن شوید ربات در آن کانال «مدیر» با دسترسی ارسال پیام است."
        )


async def on_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی ربات به گفت‌وگو/کانالی اضافه یا حذف شود، شناسه‌ی آن برای پیکربندی لاگ می‌شود."""
    cm = update.my_chat_member
    log.info("my_chat_member: chat_id=%s type=%s status %s → %s",
             cm.chat.id, cm.chat.type, cm.old_chat_member.status, cm.new_chat_member.status)
    if cm.new_chat_member.status in ("administrator", "member") and cm.chat.type == "channel":
        try:
            await context.bot.send_message(
                cm.chat.id,
                "✅ دستیار تشخیص دوگانه به کانال اضافه شد.\n"
                "برای فعال‌شدن ارسال خودکار، شناسه‌ی زیر را در TELEGRAM_CHANNEL_ID بگذارید:\n"
                f"`{cm.chat.id}`",
                parse_mode="Markdown",
            )
        except Exception:
            pass


async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شناسه‌ی کانال‌هایی که در آن‌ها مدیر است را لاگ می‌کند (کشف TELEGRAM_CHANNEL_ID)."""
    log.info("channel_post from chat_id=%s title=%s",
             update.channel_post.chat.id, update.channel_post.chat.title)


# ---------------- راه‌اندازی ----------------

def ensure_index():
    if store.manifest_matches():
        log.info("ایندکس آماده و به‌روز پیدا شد.")
        return
    log.info("ایندکس موجود نیست یا قدیمی است؛ در حال ساخت...")
    from scripts import build_index
    build_index.main()


def main():
    ensure_index()
    # پیش‌گرم کردن مدل امبدینگ تا اولین پیام کاربر سریع پاسخ بگیرد
    log.info("پیش‌گرم کردن مدل امبدینگ...")
    pipeline.answer("آماده‌سازی")
    log.info("مدل آماده است.")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("risk", cmd_risk))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("post_tip", cmd_post_tip))
    app.add_handler(CommandHandler("post_digest", cmd_post_digest))
    app.add_handler(CommandHandler("channel_status", cmd_channel_status))
    app.add_handler(CallbackQueryHandler(on_risk_button, pattern=r"^risk:\d$"))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, on_message))
    from telegram.ext import ChatMemberHandler
    app.add_handler(ChatMemberHandler(on_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, on_channel_post))

    # ---------- ارسال خودکار به کانال ----------
    if config.TELEGRAM_CHANNEL_ID and app.job_queue:
        hh, mm = (int(x) for x in config.TELEGRAM_TIP_TIME.split(":"))
        dh, dm = (int(x) for x in config.TELEGRAM_DIGEST_TIME.split(":"))
        app.job_queue.run_daily(
            job_daily_tip, time=dt_time(hh, mm, tzinfo=TEHRAN_TZ), name="daily_tip")
        app.job_queue.run_daily(
            job_weekly_digest, time=dt_time(dh, dm, tzinfo=TEHRAN_TZ), name="weekly_digest_check")
        log.info("زمان‌بندی کانال فعال شد: پست آموزشی روزانه %s و بررسی رصد هفتگی %s (به وقت تهران) → %s",
                 config.TELEGRAM_TIP_TIME, config.TELEGRAM_DIGEST_TIME, config.TELEGRAM_CHANNEL_ID)
    else:
        log.info("TELEGRAM_CHANNEL_ID تنظیم نشده؛ ارسال خودکار غیرفعال است.")

    log.info("ربات تلگرام راه‌اندازی می‌شود (long polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
