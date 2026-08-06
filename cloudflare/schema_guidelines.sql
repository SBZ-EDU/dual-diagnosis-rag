CREATE TABLE IF NOT EXISTS guidelines (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, organization TEXT, country TEXT,
 language TEXT, year INTEGER, url TEXT NOT NULL, tags TEXT NOT NULL,
 audience TEXT, status TEXT, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_guidelines_country ON guidelines(country);
CREATE INDEX IF NOT EXISTS idx_guidelines_audience ON guidelines(audience);
