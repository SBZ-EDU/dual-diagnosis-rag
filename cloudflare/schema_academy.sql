CREATE TABLE IF NOT EXISTS learning_progress (
  learner_id TEXT NOT NULL,
  audience TEXT NOT NULL,
  module_id TEXT NOT NULL,
  completed_at TEXT NOT NULL,
  score INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (learner_id, module_id)
);
CREATE TABLE IF NOT EXISTS certificates (
  id TEXT PRIMARY KEY,
  learner_id TEXT NOT NULL,
  audience TEXT NOT NULL,
  issued_at TEXT NOT NULL,
  modules_count INTEGER NOT NULL,
  verification_code TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_cert_verify ON certificates(verification_code);
