import fitz
import pytesseract
from PIL import Image
import docx2txt
import langdetect
import google.generativeai as genai
import os
import mimetypes
import re

from ragmodel.config import GEMINI_API_KEY, MODEL

genai.configure(api_key=GEMINI_API_KEY)

# ---------------------------
# Detect type
# ---------------------------
def detect_file_type(path):
    mime = mimetypes.guess_type(path)[0]
    if mime is None:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf": return "pdf"
        if ext in [".jpg", ".jpeg", ".png"]: return "image"
        if ext == ".docx": return "docx"
        return "text"
    if "pdf" in mime: return "pdf"
    if "image" in mime: return "image"
    if "word" in mime or "docx" in mime: return "docx"
    return "text"

# ---------------------------
# Readers
# ---------------------------
def read_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

def read_image(path):
    img = Image.open(path)
    return pytesseract.image_to_string(img).strip()

def read_docx(path):
    return docx2txt.process(path).strip()

def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()

def read_file(path):
    t = detect_file_type(path)
    if t == "pdf": return read_pdf(path)
    if t == "image": return read_image(path)
    if t == "docx": return read_docx(path)
    return read_txt(path)

# ---------------------------
# Translate JD if not English
# ---------------------------
def detect_lang(text):
    try:
        return langdetect.detect(text)
    except:
        return "en"

def translate_to_en(text):
    if detect_lang(text) == "en":
        return text

    prompt = f"""
Translate this job posting to English.
Do NOT rewrite or reorganize. Keep meaning exactly same.

TEXT:
{text}
"""
    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    return resp.text.strip()

# ---------------------------
# Clean
# ---------------------------
def clean_text(t):
    t = t.replace("\t", " ").replace("\r", " ")
    t = re.sub(r"\s+", " ", t)
    return t.strip()

# ---------------------------
# Split JD
# ---------------------------
def split_jd_blocks(text):
    rules = [
        r"(JOB DESCRIPTION|ABOUT THE ROLE)",
        r"(REQUIREMENTS|REQUIRED SKILLS)",
        r"(RESPONSIBILITIES|WHAT YOU WILL DO)",
        r"(TECH STACK|TECHNOLOGIES|TOOLS)"
    ]
    pattern = "(" + "|".join(rules) + ")"
    parts = re.split(pattern, text, flags=re.I)

    if len(parts) > 1:
        # FIX: đảm bảo tất cả phần tử đều là string
        clean_parts = [(p if isinstance(p, str) else "") for p in parts]
        return "\n".join(clean_parts)

    # fallback LLM
    prompt = f"""
Split this job posting into blocks:
- job_description
- required_skills
- responsibilities
- tech_stack

Do NOT rewrite, only segment.

TEXT:
{text}
"""
    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    return resp.text.strip()

# ---------------------------
# MAIN ENTRYPOINT FOR JD
# ---------------------------
def preprocess_jd(path_or_text: str):
    # 1) Determine whether input is file or raw string
    if os.path.exists(path_or_text):
        raw = read_file(path_or_text)
    else:
        raw = path_or_text

    raw = translate_to_en(raw)
    raw = clean_text(raw)
    blocks = split_jd_blocks(raw)
    return blocks
