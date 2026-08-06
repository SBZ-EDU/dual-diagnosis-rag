CREATE TABLE IF NOT EXISTS research_papers (
 openalex_id TEXT PRIMARY KEY, doi TEXT, title TEXT NOT NULL, abstract TEXT,
 year INTEGER, date TEXT, language TEXT, journal TEXT, url TEXT,
 open_access INTEGER NOT NULL DEFAULT 0, corpus TEXT NOT NULL,
 iran_affiliated INTEGER NOT NULL DEFAULT 0, treatment_tags TEXT NOT NULL,
 type TEXT, cited_by_count INTEGER DEFAULT 0, source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_research_corpus ON research_papers(corpus);
CREATE INDEX IF NOT EXISTS idx_research_year ON research_papers(year DESC);
CREATE INDEX IF NOT EXISTS idx_research_language ON research_papers(language);
