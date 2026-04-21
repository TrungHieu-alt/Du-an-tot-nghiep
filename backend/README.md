
# 🧠 AI Job Matching System (2-Way RAG with Gemini + LlamaIndex + Chroma)

## 🚀 Overview  
Đây là hệ thống **RAG (Retrieval-Augmented Generation)** hai chiều, cho phép:  

- 🔹 **Find Best Candidates** → khi đầu vào là **Job Description (JD)**  
- 🔹 **Find Best Jobs** → khi đầu vào là **CV (Resume)**  

Hệ thống sử dụng:
- **Gemini 2.5 Flash** để trích xuất và phân tích dữ liệu ngữ nghĩa (semantic parsing & reasoning)  
- **LlamaIndex** làm tầng quản lý vector index, retrieval và orchestration  
- **ChromaDB** làm **persistent vector store** để lưu embeddings  
- **SentenceTransformer (MiniLM)** để tạo embedding (vector hóa nội dung semantic)  

Toàn bộ workflow chạy **hoàn toàn local**, chỉ gọi Gemini API ở các bước parsing & reasoning.

---

## ⚙️ Workflow tổng quan

```text
            +-------------------+
            |   CV / JD Input   |
            +-------------------+
                     ↓
              (1) Gemini Parse
                     ↓
            +-------------------+
            |  JSON Semantic     |
            +-------------------+
                     ↓
           (2) json_to_text_auto
                     ↓
           +---------------------+
           |  Embedding (MiniLM) |
           |  + Chroma Storage   |
           +---------------------+
                     ↓
            (3) Retrieval (RAG)
                     ↓
            +--------------------+
            |  Gemini Reasoning  |
            |  (Score + Reason)  |
            +--------------------+
                     ↓
            🔁 Output: Ranked list
```

### 🔄 Hai hướng pipeline:
| Chiều | Input | Collection được truy vấn | Output |
|-------|--------|---------------------------|---------|
| JD → CV | JD text | `cv_collection` | Top ứng viên phù hợp |
| CV → JD | CV file | `jd_collection` | Top công việc phù hợp |

---

## 🧩 File structure

```
project/
│
├── embedder.py          # JSON → Text semantic (CV/JD)
├── li_adapter.py        # Tích hợp LlamaIndex + Chroma
├── vector_store.py      # Wrapper gọi adapter
├── resume_parser.py     # Gemini parse resume (CV)
├── jd_parser.py         # Gemini parse job description
├── logic_matcher.py     # Gemini đánh giá CV↔JD (reasoning)
└── main_refactored_v3.py# Entry point chính (2 chiều)
```

---

## 🔧 Installation

```bash
pip install llama-index-core llama-index-embeddings-huggingface \
            llama-index-vector-stores-chroma sentence-transformers \
            chromadb google-generativeai python-dotenv
```

Tạo file `.env`:

```
GEMINI_API_KEY=your_api_key_here
```

---

## 🗂 Folder structure runtime

```
cv_folder/
 ├── resume1.pdf
 ├── resume2.pdf
jd_folder/
 ├── job1.txt
 ├── job2.txt
```

---

## 🧠 How it works

### 1️⃣ Parsing Layer (Gemini)
- `resume_parser.py` → đọc PDF, OCR nếu cần → trích thông tin theo schema JSON (skills, education, projects, …)  
- `jd_parser.py` → trích xuất các trường chính từ văn bản JD (requirements, tech stack, experience, …)

Ví dụ output JSON:
```json
{
  "title": "Backend Developer",
  "summary": "Build and maintain scalable APIs",
  "requirements": ["Node.js", "Express", "MySQL"],
  "tech_stack": ["Docker", "AWS"]
}
```

---

### 2️⃣ Embedding & Storage Layer (LlamaIndex + Chroma)
- `json_to_text_auto()` → chuyển JSON semantic thành text mô tả tự nhiên  
- `upsert_json_doc()` → tự embed text, lưu vào `chroma_db/` với metadata `_raw_json` để tra cứu sau

✅ Model dùng: `sentence-transformers/all-MiniLM-L6-v2`  
✅ Store: `Chroma PersistentClient` → dữ liệu bền vững giữa các lần chạy

---

### 3️⃣ Retrieval Layer
- `query_topk(collection_name, query_text, top_k)`  
→ Tìm **Top-K** vectors gần nhất dựa trên cosine similarity.

Trả về `NodeWithScore[]` chứa:
```python
node.node.get_text()
node.score
node.node.metadata["_raw_json"]
```

---

### 4️⃣ Reasoning Layer (Gemini)
- `logic_matcher.py` → LLM đọc JD + CV để đánh giá mức độ phù hợp:
  - score (0–100)
  - matched_skills / missing_skills
  - reason (1–2 câu)
  
Ví dụ output:
```json
{
  "score": 87,
  "matched_skills": ["Node.js", "SQL", "Docker"],
  "missing_skills": ["AWS"],
  "reason": "The candidate matches all backend skills but lacks cloud experience."
}
```

---

## 🚀 Running

### ➤ Build Indexes
```python
index_all_cvs("cv_folder")
index_all_jds("jd_folder")
```

### ➤ Find Best Candidates (JD → CV)
```python
jd_text = """
Hiring Backend Developer skilled in Node.js, SQL, and API design.
2+ years experience. Familiar with Docker and AWS is a plus.
"""
find_best_candidates(jd_text)
```

### ➤ Find Best Jobs (CV → JD)
```python
cv_path = "cv_folder/sample_resume.pdf"
find_best_jobs(cv_path)
```

---

## 🧮 Output example

```
🏆 TOP MATCHED CANDIDATES

#1 resume_hieu.pdf | LLM Score 92
Reason: Matches Node.js, Express, and MySQL. Strong backend experience.

#2 resume_linh.pdf | LLM Score 85
Reason: Good backend knowledge but lacks SQL proficiency.

🏆 TOP MATCHED JOBS

#1 job_backend_lead.txt | LLM Score 88
Reason: JD aligns well with candidate’s backend stack and experience.
```

---

## 💡 Highlights

✅ **Two-way semantic RAG**: JD↔CV  
✅ **Persistent Vector Store** (ChromaDB)  
✅ **Structured JSON parsing** (Gemini schema)  
✅ **LlamaIndex orchestration** (embed, retrieve, rank)  
✅ **Explainable output** (score + reasoning)  
---

## 📦 Future Extensions
- 🔹 Add hybrid retrieval (keyword + vector)
- 🔹 Train local reranker (cross-encoder)
- 🔹 Web UI (Streamlit / FastAPI)
- 🔹 Role-based filtering (salary, location, remote)

---

## 🧭 Summary

> **RAG Architecture**
>
> ```
> Gemini Parser → JSON → LlamaIndex → Chroma → Retrieval → Gemini Reasoning
> ```
>
> **Use it both ways:**
> - `find_best_candidates(JD)` → top matching CVs  
> - `find_best_jobs(CV)` → top matching JDs  

