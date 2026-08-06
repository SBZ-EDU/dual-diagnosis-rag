"""موتور شفاف پایش خطر؛ ابزار کمک‌تصمیم است، نه تشخیص یا تجویز خودکار."""
from datetime import datetime, timezone

RED_FLAGS = {"suicidal_plan", "severe_withdrawal", "violent_intent", "catatonia", "delirium"}

def assess(data: dict) -> dict:
    """امتیازها ۰ تا ۴ هستند؛ flags فهرست علائم هشدار فوری است."""
    fields = ["psychosis", "suicide", "violence", "withdrawal", "substance_use", "sleep_loss", "nonadherence"]
    x = {k: max(0, min(4, int(data.get(k, 0)))) for k in fields}
    flags = set(data.get("flags", []))
    score = (x["psychosis"]*3 + x["suicide"]*4 + x["violence"]*3 + x["withdrawal"]*3 +
             x["substance_use"]*2 + x["sleep_loss"]*2 + x["nonadherence"]*2)
    immediate = bool(flags & RED_FLAGS) or x["suicide"] == 4 or x["withdrawal"] == 4
    if immediate:
        level, action = "بحرانی", "ارزیابی فوری حضوری/اورژانس و تماس با تیم درمان؛ بیمار تنها نماند."
    elif score >= 45:
        level, action = "خیلی بالا", "بازبینی همان‌روز توسط روان‌پزشک و به‌روزرسانی طرح ایمنی/درمان."
    elif score >= 28:
        level, action = "بالا", "تماس با تیم درمان طی ۲۴ ساعت و افزایش دفعات پایش."
    elif score >= 14:
        level, action = "متوسط", "بازبینی بالینی طی ۷۲ ساعت و مقایسه با خط پایه."
    else:
        level, action = "پایین", "ادامه پایش برنامه‌ریزی‌شده؛ هر تغییر ناگهانی را گزارش کنید."
    return {"timestamp": datetime.now(timezone.utc).isoformat(), "score": score, "level": level,
            "action": action, "red_flags": sorted(flags & RED_FLAGS), "inputs": x,
            "disclaimer": "این خروجی جایگزین ارزیابی پزشک نیست و نباید خودکار دارو را تغییر دهد."}
