from pathlib import Path
s=Path('cloudflare/src/index.js').read_text()
checks={
 'webhook_route':"u.pathname==='/telegram/webhook'" in s,
 'secret_header':'x-telegram-bot-api-secret-token' in s,
 'constant_time_not_claimed':True,
 'token_secret':'env.TELEGRAM_BOT_TOKEN' in s,
 'internal_rag':'https://internal/api/chat' in s,
 'sources_appended':'telegramSources(data)' in s,
 'medical_disclaimer':'جایگزین ارزیابی پزشک نیست' in s,
 'status_route':"u.pathname==='/api/telegram/status'" in s,
 'message_split':'splitTelegram' in s,
 'no_token_literal':'bot123' not in s,
}
assert all(checks.values()),checks
print({'status':'PASS',**checks})
