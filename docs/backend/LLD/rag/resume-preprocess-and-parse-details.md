# LLD: Resume Preprocess and Parse Details

## Source Anchors
- `backend/ragmodel/dataPreprocess/resumePreprocess.py`
- `backend/ragmodel/dataPreprocess/resumeParser.py`

## Scope Boundary
Owns CV text preprocessing and CV parsing contract only.
Embedding and vector persistence are owned elsewhere.

## Preprocess Entry
Function:
- `preprocess_resume(path_or_text: str)`

Behavior:
1. If input path exists on disk, read file by detected type.
2. Else treat input as plain text.
3. Translate to English if language detector says non-English.
4. Normalize whitespace with `clean_text`.
5. Segment content via rule-based split with LLM fallback.

## File Type Routing
`detect_file_type` maps to:
- PDF -> `read_pdf` (PyMuPDF)
- image -> `read_image` (PIL + pytesseract OCR)
- DOCX -> `read_docx` (`docx2txt`)
- fallback text -> `read_txt`

## Translation Contract
- Uses Gemini model configured in `ragmodel/config.py`.
- Prompt asks for exact meaning preservation and no summarization.
- If language detection fails, defaults to `en` and skips translation.

## Block Segmentation Contract
Primary path:
- regex split with headers: SUMMARY/PROFILE, SKILLS, EXPERIENCE, PROJECTS, EDUCATION.

Fallback path:
- LLM prompt requests segmented blocks without rewriting.

Output:
- a cleaned block-form text string, not structured JSON.

## Parser Contract (`parse_resume`)
Input:
- preprocessed CV text

Output JSON keys (strict target):
- `summary`
- `experience`
- `job_title`
- `skills` (list of strings)
- `full_text`
- `location`

Operational behavior:
- removes markdown fences from model output before JSON parse.
- raises exception on invalid JSON.

## Failure Modes
- OCR/file read failure
- Gemini API failure in translation/split/parse
- Invalid JSON from parser output

Current handling:
- exceptions bubble to repository/service, then to API as upload failure.

## Related LLD
- CV ingestion orchestration: `../cv/cv-upload-parse-embed-store-flow.md`
- Embedding contract: `embedding-and-chromadb-metadata-contract.md`
