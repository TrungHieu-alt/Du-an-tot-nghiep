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
