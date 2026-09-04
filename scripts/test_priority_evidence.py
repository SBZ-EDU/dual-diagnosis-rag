import json
from pathlib import Path
P=Path('data/evidence/priority_evidence_100.jsonl')
rows=[json.loads(x) for x in P.read_text(encoding='utf-8').splitlines() if x.strip()]
assert len(rows)==100
assert len({x['openalex_id'] for x in rows})==100
assert all(not x['is_retracted'] for x in rows)
assert all(2015 <= x['year'] <= 2026 for x in rows)
assert all(x['topic_hits']>=2 for x in rows)
assert sum(x['open_access'] for x in rows)>=80
assert all(x['screening_status']=='automated_priority_not_clinician_approved' for x in rows)
print({'status':'PASS','records':len(rows),'unique':100,'retracted':0,'open_access':sum(x['open_access'] for x in rows),'pdf':sum(bool(x['pdf_url']) for x in rows)})
