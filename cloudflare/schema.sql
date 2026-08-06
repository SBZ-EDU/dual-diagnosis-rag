CREATE TABLE IF NOT EXISTS assessments (id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, created_at TEXT NOT NULL, score INTEGER NOT NULL, level TEXT NOT NULL, payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_assessments_patient_time ON assessments(patient_id, created_at DESC);
CREATE TABLE IF NOT EXISTS alerts (id TEXT PRIMARY KEY, assessment_id TEXT NOT NULL, patient_id TEXT NOT NULL, created_at TEXT NOT NULL, level TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open');
CREATE INDEX IF NOT EXISTS idx_alerts_status_time ON alerts(status, created_at DESC);
