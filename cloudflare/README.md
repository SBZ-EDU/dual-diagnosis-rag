# Cloudflare deployment
Separate Worker + D1 deployment. Existing Workers/databases are not modified.

```bash
npx wrangler d1 execute dual-diagnosis-rag-db --remote --file schema.sql
npx wrangler secret put HF_TOKEN
npx wrangler secret put PATIENT_SALT
npx wrangler deploy
```

The UI exposes `/api/risk` backed by D1 and `/api/chat` backed by Hugging Face. Never store direct identifiers or medical names.
