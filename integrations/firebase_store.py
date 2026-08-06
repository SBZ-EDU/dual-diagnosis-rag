"""ذخیره امن ارزیابی‌ها در Firestore؛ فقط در سمت سرور استفاده شود."""
from __future__ import annotations
import hashlib, logging, os
from datetime import datetime, timezone

log = logging.getLogger(__name__)
_db = None

def enabled() -> bool:
    return os.getenv("FIREBASE_ENABLED", "0") == "1"

def _client():
    global _db
    if _db is not None: return _db
    if not enabled(): return None
    import firebase_admin
    from firebase_admin import credentials, firestore
    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        cred = credentials.Certificate(cred_path) if cred_path else credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"projectId": os.getenv("FIREBASE_PROJECT_ID")})
    _db = firestore.client()
    return _db

def pseudonym(raw_id: str) -> str:
    salt = os.environ.get("PATIENT_ID_SALT")
    if not salt: raise RuntimeError("PATIENT_ID_SALT تنظیم نشده است")
    return hashlib.sha256(f"{salt}:{raw_id}".encode()).hexdigest()[:32]

def save_assessment(patient_ref: str, result: dict, clinician_uid: str = "server") -> str | None:
    db = _client()
    if db is None: return None
    pid = pseudonym(patient_ref)
    payload = {**result, "patientId": pid, "clinicianUid": clinician_uid,
               "createdAt": datetime.now(timezone.utc), "schemaVersion": 1}
    _, ref = db.collection("patients").document(pid).collection("assessments").add(payload)
    db.collection("patients").document(pid).set({"updatedAt": payload["createdAt"]}, merge=True)
    if result.get("level") in {"بالا", "خیلی بالا", "بحرانی"}:
        db.collection("alerts").add({"patientId": pid, "assessmentId": ref.id,
            "level": result["level"], "status": "open", "createdAt": payload["createdAt"]})
    return ref.id

def recent_assessments(patient_ref: str, limit: int = 30) -> list[dict]:
    db = _client()
    if db is None: return []
    pid = pseudonym(patient_ref)
    q = (db.collection("patients").document(pid).collection("assessments")
         .order_by("createdAt", direction="DESCENDING").limit(limit))
    return [{"id": d.id, **d.to_dict()} for d in q.stream()]
