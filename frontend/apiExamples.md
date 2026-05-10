# API Integration Examples

## 1. Search Jobs
**Endpoint:** `GET /api/jobs`

**Parameters:**
- `q`: Search keyword (string)
- `location`: City/Region (string)
- `sort`: `relevance`, `newest`, `salary_high`, `salary_low`
- `cv_id`: (Optional) ID of selected CV for matching
- `page`: Page number
- `filters[level]`: Array of experience levels
- `filters[type]`: Array of job types

**Response:**
```json
{
  "data": [
    {
      "id": "1",
      "title": "Senior Frontend Developer",
      "match": {
        "score": 95,
        "reason": "Skills matched: React, TypeScript"
      }
      // ... other job fields
    }
  ],
  "meta": { "total": 120, "page": 1, "limit": 10 }
}
```

## 2. Search Candidates
**Endpoint:** `GET /api/candidates`

**Parameters:**
- `q`: Search keyword
- `req_id`: (Optional) ID of Job Requirement for matching
- `sort`: `relevance`, `exp_high`, `exp_low`
- `filters[exp]`: Experience levels
- `filters[availability]`: Availability status

**Response:**
```json
{
  "data": [
    {
      "id": "c_1",
      "name": "Nguyen Van A",
      "match": {
        "score": 88,
        "reason": "Experience level matched: Senior"
      }
      // ... candidate fields
    }
  ]
}
```

## 3. Match Details (Optional)
If matching logic is heavy, use a separate endpoint.

**Endpoint:** `GET /api/match-jobs`
**Query:** `?cvId=...&jobIds=1,2,3`

**Endpoint:** `GET /api/match-candidates`
**Query:** `?reqId=...&candidateIds=10,11,12`

---

## V2 Prototype Endpoints (Postgres + pgvector)

All ID fields are **integers** (BigInt in Postgres), not Mongo `_id` strings.
Enum values must match the V2 CHECK constraints exactly:
* `location ∈ {ha_noi, tp_hcm, da_nang}`
* `job_type ∈ {remote, fulltime, parttime}`
* `seniority ∈ {intern, fresher, junior, mid, senior, lead}`
* `education ∈ {lop_9, lop_12, dai_hoc, thac_si, tien_si}`

### Catalog browse

```bash
# Paginated list (default limit=50, max 200)
curl "http://localhost:8000/api/v2/prototype/catalog/jobs?limit=10&offset=0"
curl "http://localhost:8000/api/v2/prototype/catalog/cvs?limit=10&offset=0"

# Single record (404 if not found)
curl "http://localhost:8000/api/v2/prototype/catalog/jobs/4001"
curl "http://localhost:8000/api/v2/prototype/catalog/cvs/3001"
```

### Catalog semantic search

```bash
# Free-text only (sane defaults: top_k=20, blend_skills=0.3)
curl -X POST "http://localhost:8000/api/v2/prototype/catalog/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{"q":"backend devops"}'

# With filters (any combination of location/job_type/seniority)
curl -X POST "http://localhost:8000/api/v2/prototype/catalog/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "q":"engineer",
    "location":"ha_noi",
    "job_type":"remote",
    "seniority":"senior",
    "top_k":10,
    "blend_skills":0.4
  }'

# CV side mirrors job side
curl -X POST "http://localhost:8000/api/v2/prototype/catalog/cvs/search" \
  -H "Content-Type: application/json" \
  -d '{"q":"python kubernetes","seniority":"senior"}'
```

**Response shape**:
```json
{
  "items": [
    {
      "job_id": 4001,
      "title": "Senior Backend DevOps Engineer",
      "location": "ha_noi",
      "job_type": "remote",
      "seniority": "senior",
      "skills": ["python","docker","kubernetes","aws","postgres"],
      "score": 0.482
    }
  ],
  "total": 3
}
```

### Run matching (sync, no persistence)

```bash
# Anchor a job → top-K matching CVs
curl -X POST "http://localhost:8000/api/v2/prototype/matching/job/4001/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":5,"min_score":0.7}'

# Anchor a CV → top-K matching jobs
curl -X POST "http://localhost:8000/api/v2/prototype/matching/cv/3001/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":5,"min_score":0.7}'
```
