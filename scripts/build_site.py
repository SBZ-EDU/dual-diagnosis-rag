#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تولید protocol_page.js از سایت مخزن پروتکل (index.html + style.css + ویجت گفت‌وگو).

خروجی: cloudflare/src/protocol_page.js — صفحه‌ی کاملِ تک‌فایل برای ورکر کلودفلر.
اجرا:  python scripts/build_site.py --protocol ../dual-diagnosis-protocol
"""
import argparse
import json
import re
from pathlib import Path

WIDGET = """

<!-- ویجگت گفت‌وگوی فارسی — متصل به دستیار کلودفلر (dual-diagnosis-clinical-hub) -->
<script>
(function () {
  var API = "/api/chat";
  var DISCLAIMER = "\\n\\n⚠️ این پاسخ جایگزین مشاوره پزشک نیست.";
  var btn = document.createElement("button");
  btn.id = "ddx-chat-btn"; btn.type = "button"; btn.textContent = "💬 پرسش از دستیار";
  var panel = document.createElement("div"); panel.id = "ddx-chat-panel";
  panel.innerHTML = '<div id="ddx-chat-head"><b>دستیار تشخیص دوگانه</b>' +
    '<button id="ddx-chat-close" type="button" aria-label="بستن">×</button></div>' +
    '<div id="ddx-chat-msgs"></div>' +
    '<div id="ddx-chat-chips"></div>' +
    '<form id="ddx-chat-form"><input id="ddx-chat-in" placeholder="سؤال خود را فارسی بنویسید…" ' +
    'autocomplete="off" maxlength="500"><button id="ddx-chat-send" type="submit">ارسال</button></form>';
  document.body.appendChild(btn); document.body.appendChild(panel);
  var CHIPS = ["درمان یکپارچه چیست؟", "علائم هشدار عود", "کلوزاپین چه زمانی؟", "چطور از همراه حمایت کنم؟"];
  var chipsBox = panel.querySelector("#ddx-chat-chips");
  CHIPS.forEach(function (c) {
    var el = document.createElement("button");
    el.type = "button"; el.className = "ddx-chip"; el.textContent = c;
    el.onclick = function () {
      var inp = panel.querySelector("#ddx-chat-in");
      inp.value = c;
      panel.querySelector("#ddx-chat-form").dispatchEvent(new Event("submit", {cancelable: true}));
    };
    chipsBox.appendChild(el);
  });
  var msgs = panel.querySelector("#ddx-chat-msgs");
  function add(text, who) {
    var d = document.createElement("div"); d.className = "ddx-msg " + who;
    d.textContent = text; msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; return d;
  }
  add("سلام! سؤال بالینی خود را درباره‌ی تشخیص دوگانه بپرسید؛ پاسخ فارسی و با ذکر منابع علمی داده می‌شود.", "bot");
  btn.onclick = function () { panel.classList.toggle("open");
    if (panel.classList.contains("open")) panel.querySelector("#ddx-chat-in").focus(); };
  panel.querySelector("#ddx-chat-close").onclick = function () { panel.classList.remove("open"); };
  panel.querySelector("#ddx-chat-form").onsubmit = function (e) {
    e.preventDefault();
    var inp = panel.querySelector("#ddx-chat-in"), q = inp.value.trim();
    if (!q) return; inp.value = "";
    add(q, "user");
    var busy = add("در حال پاسخ‌گویی…", "bot");
    panel.querySelector("#ddx-chat-send").disabled = true;
    fetch(API, { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ question: q, role: "patient" }) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        busy.textContent = (d.answer || d.error || "پاسخی دریافت نشد.") +
          (d.answer ? DISCLAIMER : "");
        msgs.scrollTop = msgs.scrollHeight;
      })
      .catch(function () {
        busy.textContent = "خطای ارتباط با دستیار. اتصال اینترنت را بررسی و دوباره تلاش کنید.";
      })
      .finally(function () { panel.querySelector("#ddx-chat-send").disabled = false; });
  };
})();
</script>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", default="../dual-diagnosis-protocol", help="مسیر مخزن پروتکل")
    args = ap.parse_args()
    root = Path(args.protocol)
    html = (root / "index.html").read_text(encoding="utf-8")
    css = (root / "style.css").read_text(encoding="utf-8")

    # ۱) استایل داخل‌خطی (صفحه‌ی تک‌فایل برای ورکر)
    html = re.sub(
        r'<link\s+rel="stylesheet"\s+href="style\.css"\s*/?>',
        "<style>\n" + css + "\n</style>",
        html, count=1)

    # ۲) ویجت گفت‌وگو قبل از </body>
    if "ddx-chat-btn" not in html:
        html = html.replace("</body>", WIDGET + "\n</body>", 1)

    out = (
        "// ساخته‌شده به‌صورت خودکار از SBZ-EDU/dual-diagnosis-protocol\n"
        "// (ویجت گفت‌وگو منبع واحد است؛ API نسبی برای همین مبدأ)\n"
        "export const PROTOCOL_HTML = " + json.dumps(html, ensure_ascii=False) + ";\n"
    )
    dest = Path(__file__).resolve().parent.parent / "cloudflare" / "src" / "protocol_page.js"
    dest.write_text(out, encoding="utf-8")
    print(f"OK: {dest} ({len(html)} chars HTML)")


if __name__ == "__main__":
    main()
