CREATE TABLE IF NOT EXISTS articles (
  doi TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  abstract TEXT,
  journal TEXT,
  published TEXT,
  url TEXT,
  source TEXT NOT NULL DEFAULT 'Crossref',
  fetched_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published DESC);
