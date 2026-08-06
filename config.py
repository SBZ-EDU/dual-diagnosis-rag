"""
تنظیمات پروژه‌ی RAG تشخیص دوگانه.
همه‌ی مقادیر قابل تغییر از طریق متغیرهای محیطی هستند.
"""
import os

# ---------- پایگاه دانش ----------
# مسیر پوشه‌ی داده‌ها (پروتکل، مقالات، سابقه بیمار، بازخورد)
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
PROTOCOL_FILE = os.path.join(DATA_DIR, "protocol.md")

# پوشه‌های منابع اضافه (مقاله، سابقه بیمار، بازخورد کاربران)
SOURCES = {
    "articles": os.path.join(DATA_DIR, "articles"),
    "guidelines": os.path.join(DATA_DIR, "guidelines"),
    "patient_history": os.path.join(DATA_DIR, "patient_history"),
    "feedback": os.path.join(DATA_DIR, "feedback"),
}

# ---------- ایندکس برداری ----------
INDEX_DIR = os.getenv("INDEX_DIR", os.path.join(os.path.dirname(__file__), "index"))
CHUNKS_FILE = os.path.join(INDEX_DIR, "chunks.json")
VECTORS_FILE = os.path.join(INDEX_DIR, "vectors.npz")

# اندازه‌ی قطعه و هم‌پوشانی برای شکستن متن
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))        # کاراکتر
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))   # کاراکتر

# ---------- مدل امبدینگ ----------
# چندزبانه (شامل فارسی)، سبک و سریع روی CPU
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
TOP_K = int(os.getenv("TOP_K", "5"))

# ---------- مدل مولد (هوش مصنوعی) ----------
# مدل سبک اوپن‌سورس روی CPU رایگان. برای لامای بزرگ‌تر روی GPU مقدار را تغییر دهید.
GEN_MODEL = os.getenv("GEN_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
USE_GENERATOR = os.getenv("USE_GENERATOR", "1") == "1"   # ۱=روشن، ۰=فقط بازیابی
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "400"))

# ---------- Weights & Biases ----------
WANDB_PROJECT = os.getenv("WANDB_PROJECT", "dual-diagnosis-rag")
WANDB_ENTITY = os.getenv("WANDB_ENTITY", "elasa2next-sosa-")
WANDB_ENABLED = bool(os.getenv("WANDB_API_KEY"))  # اگر کلید باشد، فعال می‌شود
