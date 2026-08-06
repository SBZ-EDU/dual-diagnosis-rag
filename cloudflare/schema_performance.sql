CREATE TABLE IF NOT EXISTS rag_cache (
  cache_key TEXT PRIMARY KEY,
  answer TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS api_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  endpoint TEXT NOT NULL,
  provider TEXT NOT NULL,
  latency_ms INTEGER NOT NULL,
  success INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_created ON api_usage(created_at DESC);
