# Báo cáo Test Matching V2 — 2026-05-08

## Môi trường

| Thành phần | Chi tiết |
|---|---|
| Branch | `v2` |
| Backend | FastAPI + uvicorn, `http://localhost:8000` |
| Database | PostgreSQL 16 + pgvector, port 5433 |
| Data | 10 CV, 10 JD, 9 embeddings (CV 1010 bỏ qua có chủ ý) |

---

## Cách tái tạo kết quả

> Chạy từng bước theo thứ tự. Sau bước 4 là có thể gọi các curl ở phần kịch bản bên dưới và ra đúng kết quả.

### Bước 1 — Khởi động services

```bash
docker compose up -d postgres mongo backend
```

Chờ backend healthy (thường 20–30 giây):

```bash
# chờ đến khi in ra "Backend ready"
until curl -sf http://localhost:8000/api/health > /dev/null; do sleep 3; done && echo "Backend ready"
```

### Bước 2 — Reset và seed dữ liệu gốc (5 CV + 5 JD)

Chạy từ thư mục gốc repo:

```bash
docker compose exec backend python db_v2/reset.py
```

Lệnh này drop toàn bộ schema `public`, chạy lại `migrations/001_init.sql` rồi `seeds/001_seed.sql`.
Sau bước này DB có đúng **5 CV, 5 JD, 5 CV embeddings, 5 JD embeddings**.

Kiểm tra:

```bash
docker exec jobmatcher-postgres sh -c "psql -U jobmatcher -d jobmatcher_v2 -c \"
  SELECT 'candidate_profiles_v2' AS tbl, COUNT(*) FROM candidate_profiles_v2
  UNION ALL SELECT 'job_posts_v2',            COUNT(*) FROM job_posts_v2
  UNION ALL SELECT 'candidate_embeddings_v2', COUNT(*) FROM candidate_embeddings_v2
  UNION ALL SELECT 'job_embeddings_v2',       COUNT(*) FROM job_embeddings_v2;\""
```

Kết quả mong đợi: 5 rows mỗi bảng.

### Bước 3 — Thêm dữ liệu test kịch bản (5 CV + 5 JD mới)

File: `backend/db_v2/seeds/002_extra_test_data.sql`

```bash
# copy file vào postgres container rồi chạy
docker compose cp backend/db_v2/seeds/002_extra_test_data.sql postgres:/tmp/002.sql
docker exec jobmatcher-postgres sh -c "psql -U jobmatcher -d jobmatcher_v2 -f /tmp/002.sql"
```

Output mong đợi:
```
INSERT 0 5   ← candidate_profiles_v2
INSERT 0 5   ← job_posts_v2
INSERT 0 4   ← candidate_embeddings_v2 (CV 1010 không có embedding — có chủ ý)
INSERT 0 5   ← job_embeddings_v2
```

Kiểm tra lại: mỗi bảng giờ có **10 rows** (trừ `candidate_embeddings_v2` có 9).

### Bước 4 — Xác nhận backend thấy data mới

```bash
curl -s "http://localhost:8000/api/v2/prototype/matching/job/2006/run" | python -m json.tool
```

Nếu trả về `total_candidates: 10` là data đã load đúng.

### Ghi chú về tính deterministic

- Mọi embedding trong seed dùng `array_fill(value, ARRAY[384])` — vector hằng số.
- Hai vector hằng số bất kỳ đều có cosine similarity = 1.0 (cùng hướng).
- Vì vậy **semantic score luôn = 1.0** cho mọi cặp qua hard filter; chỉ exact skill overlap tạo ra sự khác biệt về điểm số.
- Kết quả (rank, score, reasoning) là deterministic — chạy lại bao nhiêu lần cũng ra cùng số, chỉ `runtime_ms_*` thay đổi.

---

## Dữ liệu test thêm vào

File: `backend/db_v2/seeds/002_extra_test_data.sql`

### CV mới (1006–1010)

| cv_id | title | location | job_type | seniority | education | certifications | ghi chú |
|---|---|---|---|---|---|---|---|
| 1006 | Senior DevOps Engineer | ha_noi | remote | senior | dai_hoc | cka, aws_saa | match chính của JD 2006 |
| 1007 | Mid ML Engineer | tp_hcm | fulltime | mid | thac_si | — | match chính của JD 2007 |
| 1008 | Frontend Lead | ha_noi | fulltime | lead | dai_hoc | — | match chính của JD 2008 |
| 1009 | Intern Backend Developer | ha_noi | fulltime | intern | lop_12 | — | match chính của JD 2009 |
| 1010 | Mid Data Scientist | da_nang | parttime | mid | tien_si | google_ml | **KHÔNG có embeddings** |

### JD mới (2006–2010)

| job_id | title | location | job_type | seniority | education | req_certs | mục đích |
|---|---|---|---|---|---|---|---|
| 2006 | Senior DevOps Engineer | ha_noi | remote | senior | dai_hoc | cka | test cert filter + skills ranking |
| 2007 | Mid ML Engineer | tp_hcm | fulltime | mid | dai_hoc | — | test location + education hierarchy |
| 2008 | Frontend Lead | ha_noi | fulltime | lead | dai_hoc | — | test seniority filter (CV 1002 bị loại) |
| 2009 | Intern Backend Developer | ha_noi | fulltime | intern | lop_9 | — | test seniority strict = intern |
| 2010 | Mid Data Scientist | da_nang | parttime | mid | thac_si | google_ml | test missing embeddings path |

---

## Kết quả từng kịch bản

### Kịch bản 1 — JD 2006: Required certification + skills ranking

**Mục đích:** Chỉ CV có cert `cka` và `job_type=remote` mới qua filter. Ranking phân biệt bằng exact skill overlap.

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2006/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

| Kết quả | Giá trị |
|---|---|
| total_candidates | 10 |
| total_after_filter | **2** (CV 1006 và CV 1003) |
| total_returned | 2 |

| rank | cv_id | final_score | skills_score | exact matches |
|---|---|---|---|---|
| 1 | **1006** | **1.000** | 1.000 | 4: aws, docker, kubernetes, terraform |
| 2 | 1003 | 0.895 | 0.700 | 1: docker |

**Tại sao CV 1006 = 1.0:**
JD skills = `[docker, kubernetes, aws, terraform]`, CV 1006 skills = `[docker, kubernetes, aws, terraform]`.
`exact_overlap = 4/max(4,4) = 1.0` → `skills_score = 0.6×1.0 + 0.4×1.0 = 1.0`
`final_score = 0.35×1.0 + 0.35×1.0 + 0.20×1.0 + 0.10×1.0 = 1.0`

**Tại sao CV 1003 = 0.895:**
CV 1003 skills = `[python, react, postgres, docker]` → chỉ `docker` trùng.
`exact_overlap = 1/max(4,4) = 0.25` → `skills_score = 0.6×1.0 + 0.4×0.25 = 0.7`
`final_score = 0.35×1.0 + 0.35×0.7 + 0.20×1.0 + 0.10×1.0 = 0.895`

**Tại sao 8 CV còn lại bị loại:**
Các CV còn lại không phải `remote` hoặc không có cert `cka` → bị lọc ở hard filter.

**✅ Đúng:** CV 1006 rank 1 (overlap đầy đủ 4/4). CV 1003 vẫn qua filter (có cka) nhưng xếp sau vì chỉ overlap 1 skill.

---

### Kịch bản 2 — JD 2007: Location + education hierarchy

**Mục đích:** Chỉ CV ở tp_hcm, fulltime, mid mới qua. Education thac_si >= dai_hoc → pass.

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2007/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

| Kết quả | Giá trị |
|---|---|
| total_candidates | 10 |
| total_after_filter | **1** |
| total_returned | 1 |

| rank | cv_id | final_score | exact matches |
|---|---|---|---|
| 1 | **1007** | **0.965** | 3: ml, python, tensorflow |

**Tại sao CV 1007 = 0.965:**
JD skills = `[python, tensorflow, ml]`, CV 1007 skills = `[python, tensorflow, ml, pandas]`.
`exact_overlap = 3/max(3,4) = 0.75` → `skills_score = 0.6×1.0 + 0.4×0.75 = 0.9`
`final_score = 0.35×1.0 + 0.35×0.9 + 0.20×1.0 + 0.10×1.0 = 0.965`

**Tại sao 9 CV còn lại bị loại (hard filter checklist):**

| cv_id | job_type | location | seniority | education | certif | lý do bị loại |
|---|---|---|---|---|---|---|
| 1001 | fulltime≠fulltime ✓ | ha_noi≠tp_hcm | senior≠mid | — | — | location + seniority |
| 1002 | fulltime ✓ | tp_hcm ✓ | junior≠mid | — | — | seniority |
| 1003 | remote≠fulltime | — | — | — | — | job_type |
| 1004 | parttime≠fulltime | — | — | — | — | job_type |
| 1005 | fulltime ✓ | ha_noi≠tp_hcm | — | — | — | location |
| 1006 | remote≠fulltime | — | — | — | — | job_type |
| 1008 | fulltime ✓ | ha_noi≠tp_hcm | — | — | — | location |
| 1009 | fulltime ✓ | ha_noi≠tp_hcm | — | — | — | location |
| 1010 | parttime≠fulltime | — | — | — | — | job_type |

**Education hierarchy:** CV 1007 có `thac_si` (rank 3) ≥ JD yêu cầu `dai_hoc` (rank 2) → **pass**.
Thang bậc: `lop_9`(0) < `lop_12`(1) < `dai_hoc`(2) < `thac_si`(3) < `tien_si`(4).

**✅ Đúng:** 9 CV còn lại bị loại do seniority (junior/senior/lead), location (ha_noi/da_nang), hoặc job_type (remote/parttime).

---

### Kịch bản 3 — JD 2008: Seniority filter (CV 1002 junior bị loại)

**Mục đích:** CV 1002 (Junior Frontend) bị loại vì seniority không khớp (junior ≠ lead). CV 1005 (Lead, sai skills) vẫn qua filter nhưng xếp cuối.

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2008/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

| Kết quả | Giá trị |
|---|---|
| total_candidates | 10 |
| total_after_filter | **2** (CV 1008 và CV 1005) |
| total_returned | 2 |

| rank | cv_id | final_score | skills_score | ghi chú |
|---|---|---|---|---|
| 1 | **1008** | **1.000** | 1.000 | 4 skill khớp hoàn toàn |
| 2 | 1005 | 0.860 | 0.600 | 0 exact skill overlap; semantic = 1.0 đẩy score lên 0.86 |

**Tại sao CV 1008 = 1.0:**
JD skills = `[react, vue, typescript, nodejs]`, CV 1008 skills = `[react, vue, typescript, nodejs]` → overlap = 4/4 = 1.0.
`skills_score = 0.6×1.0 + 0.4×1.0 = 1.0` → `final_score = 1.0`

**Tại sao CV 1005 = 0.86 dù skills hoàn toàn khác:**
CV 1005 skills = `[python, sql, spark, ml]` → `exact_overlap = 0/4 = 0.0`
`skills_score = 0.6×1.0 + 0.4×0.0 = 0.6`
`final_score = 0.35×1.0 + 0.35×0.6 + 0.20×1.0 + 0.10×1.0 = 0.86`
Semantic score = 1.0 (do constant-fill vector) kéo tổng lên, bù cho exact skill overlap = 0.

> **Hạn chế seed data:** Constant-fill embedding vectors (`array_fill`) có cosine similarity = 1.0 với nhau — không phân biệt được ngữ nghĩa. Vì vậy CV 1005 (Data Engineer) vẫn vào top dù skills hoàn toàn lệch với JD Frontend. Dùng embeddings thật từ model thì CV 1005 sẽ có semantic score thấp và bị min_score loại.

**✅ Đúng:** CV 1002 bị lọc bởi seniority. CV 1008 rank 1. CV 1005 rank 2 nhưng chỉ do semantic score giả tạo.

---

### Kịch bản 4 — JD 2009: Intern-only pool

**Mục đích:** Seniority `intern` là strict exact match — chỉ CV 1009 qua.

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2009/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

| Kết quả | Giá trị |
|---|---|
| total_candidates | 10 |
| total_after_filter | **1** |
| total_returned | 1 |

| rank | cv_id | final_score | exact matches |
|---|---|---|---|
| 1 | **1009** | **1.000** | 2: python, sql |

**Tại sao CV 1009 = 1.0:**
JD skills = `[python, sql]`, CV 1009 skills = `[python, sql]` → overlap = 2/2 = 1.0.
Mọi component đều = 1.0 → `final_score = 1.0`

**Tại sao education pass dù CV có lop_12 và JD yêu cầu lop_9:**
`lop_12`(rank 1) ≥ `lop_9`(rank 0) → pass. Education filter là **"CV phải có bằng ít nhất bằng JD yêu cầu"**, không phải exact match.

**✅ Đúng:** 9 CV còn lại đều có seniority khác `intern` (fresher/junior/mid/senior/lead) → bị lọc.

---

### Kịch bản 5 — JD 2010: Missing embeddings

**Mục đích:** CV 1010 qua hard filter (cert google_ml, education tien_si ≥ thac_si) nhưng không có embeddings. Tất cả semantic score = 0. Chỉ exact skill overlap tạo ra điểm.

#### 5a — min_score=0.7 (default)

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2010/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

| Kết quả | Giá trị |
|---|---|
| total_after_filter | 1 |
| total_returned | **0** — CV 1010 bị lọc bởi min_score |

**✅ Đúng:** final_score = 0.14 < 0.7 → không trả về.

#### 5b — min_score=0.0 (để thấy score thực)

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/job/2010/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.0}' | python -m json.tool
```

| rank | cv_id | final_score | skills_score | ghi chú |
|---|---|---|---|---|
| 1 | **1010** | **0.140** | 0.400 | title/req_exp/req_summary = 0.0 do thiếu embeddings |

**Tại sao final_score = 0.14:**
CV 1010 không có row trong `candidate_embeddings_v2` → mọi `emb_*` = `None` → `cosine_similarity(None, ...)` = 0.
`title_score = 0`, `req_exp_score = 0`, `req_summary_score = 0`
JD skills = `[python, ml, statistics]`, CV skills = `[python, ml, statistics]` → `exact_overlap = 3/3 = 1.0`
`skills_score = 0.6×0 + 0.4×1.0 = 0.4`
`final_score = 0.35×0 + 0.35×0.4 + 0.20×0 + 0.10×0 = 0.14`

**✅ Đúng:** Hệ thống không crash. Reasoning liệt kê đủ 4 fields thiếu embedding. Score thấp do không có semantic signal.

---

### Kịch bản 6 — CV 1006 → tìm JDs phù hợp

**Mục đích:** Chiều ngược: CV tìm JD.

```bash
curl -s -X POST "http://localhost:8000/api/v2/prototype/matching/cv/1006/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}' | python -m json.tool
```

| rank | job_id | final_score | exact matches |
|---|---|---|---|
| 1 | **2006** | **1.000** | 4: aws, docker, kubernetes, terraform |
| 2 | 2003 | 0.860 | 0 (remote senior fullstack, khác skills) |

**Tại sao JD 2006 = 1.0:** Skills khớp hoàn toàn (4/4) → giống tính toán kịch bản 1.

**Tại sao JD 2003 = 0.86 dù skills khác hoàn toàn:**
JD 2003 = `[python, react, postgres]`, CV 1006 = `[docker, kubernetes, aws, terraform]` → overlap = 0.
`skills_score = 0.6×1.0 + 0.4×0 = 0.6` → `final_score = 0.35×1.0 + 0.35×0.6 + 0.20×1.0 + 0.10×1.0 = 0.86`
(Lý do tương tự kịch bản 3: semantic score = 1.0 do constant-fill vector)

**Tại sao chỉ 2 JD qua filter (từ 10 JD):**
CV 1006 là `remote`, `senior`, `dai_hoc`. Các JD phải khớp `job_type=remote`, `seniority=senior`, `education≤dai_hoc`, và không có `required_certifications` mà CV thiếu.
- JD 2006: remote, senior, dai_hoc, req_cert=[cka] — CV có cka ✓ → **pass**
- JD 2003: remote, senior, dai_hoc, req_cert=[] ✓ → **pass**
- Còn lại: fulltime/parttime hoặc seniority khác → fail

**✅ Đúng:** JD 2006 là best match. JD 2003 vẫn qua filter (remote, senior, dai_hoc, no required cert) nhưng skill overlap = 0.

---

## Tổng kết

| Kịch bản | Filter | Kết quả | Trạng thái |
|---|---|---|---|
| 1. Cert filter + skills ranking | job_type=remote, cka required | 2 pass, rank đúng theo overlap | ✅ |
| 2. Location + education hierarchy | tp_hcm, mid, thac_si≥dai_hoc | 1 pass | ✅ |
| 3. Seniority (lead vs junior) | CV 1002 junior bị loại | 2 pass, CV 1008 rank 1 | ✅ |
| 4. Intern strict seniority | intern-only | 1 pass | ✅ |
| 5a. Missing embeddings (default) | cert pass, score < 0.7 | 0 returned | ✅ |
| 5b. Missing embeddings (min=0) | cert pass | score = 0.14, reasoning đúng | ✅ |
| 6. CV→JD reverse match | remote, senior, no cert | 2 returned | ✅ |

**Unit tests:** 26/26 PASS (`tests/test_matching_v2_core.py` + `tests/test_match_v2_router.py`)

### Quan sát

- **Hard filter hoạt động chính xác:** seniority (exact), education (hierarchy), certification (subset), job_type, location (bỏ qua khi remote).
- **Ranking phân biệt đúng:** exact skill overlap là yếu tố chính tạo ra sự khác biệt giữa các CV qua filter.
- **Missing embeddings xử lý an toàn:** không crash, semantic score = 0, reasoning báo rõ fields thiếu.
- **Hạn chế seed data:** constant-fill vectors (`array_fill`) có cosine = 1.0 với nhau nên semantic score luôn = 1.0 cho mọi cặp qua filter. Để test semantic ranking thực sự cần embeddings từ model thật.
