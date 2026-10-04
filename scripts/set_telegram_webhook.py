"""Register the Cloudflare Telegram webhook without printing secrets."""
import json, os, urllib.request
TOKEN=os.getenv('TELEGRAM_BOT_TOKEN','')
SECRET=os.getenv('TELEGRAM_WEBHOOK_SECRET','')
BASE=os.getenv('TELEGRAM_WEBHOOK_BASE','https://dual-diagnosis-clinical-hub.elasa2next.workers.dev')
if not TOKEN or not SECRET: raise SystemExit('Set TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET as environment secrets.')
if len(SECRET)<16: raise SystemExit('TELEGRAM_WEBHOOK_SECRET must be at least 16 characters.')
payload=json.dumps({'url':BASE.rstrip('/')+'/telegram/webhook','secret_token':SECRET,'allowed_updates':['message','edited_message'],'drop_pending_updates':False}).encode()
req=urllib.request.Request(f'https://api.telegram.org/bot{TOKEN}/setWebhook',data=payload,headers={'content-type':'application/json','User-Agent':'DualDiagnosis-Webhook-Setup/1.0'})
with urllib.request.urlopen(req,timeout=30) as r: result=json.load(r)
print(json.dumps({'ok':result.get('ok'),'description':result.get('description'),'webhook_url':BASE.rstrip('/')+'/telegram/webhook'},ensure_ascii=False,indent=2))
