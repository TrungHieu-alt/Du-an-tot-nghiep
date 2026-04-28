import os
from dotenv import load_dotenv
load_dotenv()

MASTODON_API_BASE_URL = os.getenv("MASTODON_API_BASE_URL")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
AI_MODE = os.getenv("AI_MODE", "live").strip().lower()

# Gemini queue controls
GEMINI_QUEUE_MAXSIZE = int(os.getenv("GEMINI_QUEUE_MAXSIZE", "256"))
GEMINI_QUEUE_WORKERS = int(os.getenv("GEMINI_QUEUE_WORKERS", "2"))
GEMINI_QUEUE_TIMEOUT_SEC = float(os.getenv("GEMINI_QUEUE_TIMEOUT_SEC", "45"))
GEMINI_QUEUE_RETRIES = int(os.getenv("GEMINI_QUEUE_RETRIES", "2"))
