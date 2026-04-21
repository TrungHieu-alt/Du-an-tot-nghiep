import os
from dotenv import load_dotenv
load_dotenv()

MASTODON_API_BASE_URL = os.getenv("MASTODON_API_BASE_URL")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL="gemini-2.5-flash-lite"  
