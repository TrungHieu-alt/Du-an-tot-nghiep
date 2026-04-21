# LLD: Job Preprocess and Parse Details

## Source Anchors
- `backend/ragmodel/dataPreprocess/jobPreprocess.py`
- `backend/ragmodel/dataPreprocess/jobParser.py`

## Scope Boundary
Owns JD text preprocessing and JD parsing contract only.
Embedding/vector contracts are documented elsewhere.

## Preprocess Entry
Function:
- `preprocess_jd(path_or_text: str)`

Behavior:
1. If path exists, detect file type and read content.
2. Else treat input as text.
3. Translate to English when needed.
4. Normalize whitespace.
5. Split JD into semantic blocks with regex-first strategy.

## File Readers
Supported sources:
- PDF (PyMuPDF)
- image OCR (pytesseract)
- DOCX (docx2txt)
- text fallback

## Translation Contract
- Non-English JD text translated via Gemini prompt.
- Prompt requests no rewriting/reorganization.

## JD Block Segmentation
Rule-based headers:
- JOB DESCRIPTION / ABOUT THE ROLE
- REQUIREMENTS / REQUIRED SKILLS
- RESPONSIBILITIES / WHAT YOU WILL DO
- TECH STACK / TECHNOLOGIES / TOOLS

Fallback:
- LLM segmentation into `job_description`, `required_skills`, `responsibilities`, `tech_stack` blocks.

## Parser Contract (`parse_jd`)
Input:
- preprocessed JD text

Output JSON keys (strict target):
- `job_description`
- `job_requirement`
- `job_title`
- `skills` (list)
- `full_text`
- `location`

Behavior:
- strips code fences
- JSON parse strict, raises on invalid structure

## Failure Modes
- read/OCR failure
- translation/parsing API failure
- invalid JSON from parser output

Current behavior:
- exceptions bubble to repository/service upload handlers.

## Related LLD
- Job ingestion orchestration: `../jobs/job-upload-parse-embed-store-flow.md`
- Embedding/vector contract: `embedding-and-chromadb-metadata-contract.md`
