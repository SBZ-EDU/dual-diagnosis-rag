"""Safe Telegram deployment diagnostics. Never prints the bot token."""
from __future__ import annotations
import importlib.util, json, os, sys, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

def get_json(url: str, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)

def main() -> int:
    checks = {}
    checks['telegram_package'] = importlib.util.find_spec('telegram') is not None
    token = config.TELEGRAM_BOT_TOKEN
    checks['token_configured'] = bool(token)
    checks['channel_configured'] = bool(config.TELEGRAM_CHANNEL_ID)
    checks['admin_ids_configured'] = bool(config.TELEGRAM_ADMIN_IDS)
    try:
        health = get_json('https://dual-diagnosis-clinical-hub.elasa2next.workers.dev/api/health')
        checks['cloudflare_rag'] = health.get('status') == 'ok'
    except Exception as e:
        checks['cloudflare_rag'] = False
        checks['cloudflare_error'] = type(e).__name__
    if token:
        try:
            me = get_json(f'https://api.telegram.org/bot{token}/getMe')
            checks['telegram_getMe'] = bool(me.get('ok'))
            result = me.get('result') or {}
            checks['bot_username'] = result.get('username')
        except urllib.error.HTTPError as e:
            checks['telegram_getMe'] = False
            checks['telegram_http_status'] = e.code
        except Exception as e:
            checks['telegram_getMe'] = False
            checks['telegram_error'] = type(e).__name__
    else:
        checks['telegram_getMe'] = False
    if token and config.TELEGRAM_CHANNEL_ID:
        try:
            chat = get_json(f'https://api.telegram.org/bot{token}/getChat?chat_id={urllib.parse.quote(config.TELEGRAM_CHANNEL_ID)}')
            checks['channel_access'] = bool(chat.get('ok'))
        except Exception as e:
            checks['channel_access'] = False
            checks['channel_error'] = type(e).__name__
    else:
        checks['channel_access'] = False
    required = ['telegram_package','token_configured','telegram_getMe','cloudflare_rag']
    checks['ready_for_private_chat'] = all(checks.get(x) for x in required)
    checks['ready_for_channel'] = checks['ready_for_private_chat'] and checks['channel_configured'] and checks['channel_access']
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    if not checks['telegram_package']:
        print('\nFIX: pip install "python-telegram-bot[job-queue]>=21.7,<22"')
    if not token:
        print('FIX: set TELEGRAM_BOT_TOKEN as a secret/environment variable.')
    if not config.TELEGRAM_CHANNEL_ID:
        print('INFO: set TELEGRAM_CHANNEL_ID only if automatic channel posting is wanted.')
    print('INFO: long polling requires an always-on process: python telegram_bot.py')
    return 0 if checks['ready_for_private_chat'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
