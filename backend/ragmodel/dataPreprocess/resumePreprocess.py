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
# Detect file type
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
# Language detect + translate
# ---------------------------
def detect_lang(text: str):
    try:
        return langdetect.detect(text)
    except:
        return "en"

def translate_to_en(text: str):
    lang = detect_lang(text)
    if lang == "en":
        return text

    prompt = f"""
Translate the following resume content to English.
Do NOT rewrite, do NOT summarize, keep meaning exactly the same.

TEXT:
{text}
"""
    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    return resp.text.strip()

# ---------------------------
# Clean text
# ---------------------------
def clean_text(t: str):
    t = t.replace("\t", " ").replace("\r", " ")
    t = re.sub(r"\s+", " ", t)
    return t.strip()

# ---------------------------
# Split resume blocks (rule first, LLM fallback)
# ---------------------------
def split_resume_blocks(text: str):
    rules = [
        r"(SUMMARY|PROFILE)",
        r"(SKILLS|TECHNICAL SKILLS)",
        r"(EXPERIENCE|WORK EXPERIENCE)",
        r"(PROJECTS)",
        r"(EDUCATION)"
    ]

    # Regex pattern to segment but still keep headers
    pattern = "(" + "|".join(rules) + ")"
    parts = re.split(pattern, text, flags=re.I)

    # =============================
    # FIX CORE ERROR: REMOVE None
    # =============================
    if parts:
        cleaned = [
            p.strip()
            for p in parts
            if p is not None and isinstance(p, str) and p.strip()
        ]

        if len(cleaned) > 1:
            return "\n".join(cleaned)

    # ----------------------------
    # Fallback LLM segmentation
    # ----------------------------
    prompt = f"""
Split the following resume into clean blocks:
SUMMARY
SKILLS
EXPERIENCE
PROJECTS
EDUCATION

Do NOT rewrite; only segment text.

TEXT:
{text}
"""
    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    return resp.text.strip()

# ---------------------------
# MAIN ENTRYPOINT FOR CV
# ---------------------------
def preprocess_resume(path_or_text: str):
    # 1) If input is a file -> read it
    if os.path.exists(path_or_text):
        raw = read_file(path_or_text)
    else:
        raw = path_or_text  # string directly

    # 2) Translate (if needed)
    raw = translate_to_en(raw)

    # 3) Clean
    raw = clean_text(raw)

    # 4) Split
    blocks = split_resume_blocks(raw)
    print("---- Resume Preprocessing Complete ----", blocks[:100])

    return blocks
