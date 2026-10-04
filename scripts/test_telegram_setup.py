from pathlib import Path
req=Path('requirements.txt').read_text()
bot=Path('telegram_bot.py').read_text()
doc=Path('scripts/telegram_doctor.py').read_text()
checks={
 'dependency':'python-telegram-bot[job-queue]' in req,
 'token_from_env':'TELEGRAM_BOT_TOKEN' in bot and 'config.TELEGRAM_BOT_TOKEN' in bot,
 'long_polling':'run_polling' in bot,
 'diagnostic_getme':'/getMe' in doc,
 'diagnostic_health':'/api/health' in doc,
 'token_not_printed':'print(token)' not in doc,
}
assert all(checks.values()),checks
print({'status':'PASS',**checks})
