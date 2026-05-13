# V2 API Examples

All ID fields are integers (`BIGINT` in PostgreSQL). Enum values must match the
backend constraints exactly:

- `location`: `ha_noi`, `tp_hcm`, `da_nang`
- `job_type`: `remote`, `fulltime`, `parttime`
- `seniority`: `intern`, `fresher`, `junior`, `mid`, `senior`, `lead`
- `education`: `lop_9`, `lop_12`, `dai_hoc`, `thac_si`, `tien_si`

## Catalog Browse

```bash
curl "http://localhost:8000/api/v2/prototype/catalog/jobs?limit=10&offset=0"
curl "http://localhost:8000/api/v2/prototype/catalog/cvs?limit=10&offset=0"
curl "http://localhost:8000/api/v2/prototype/catalog/jobs/4001"
curl "http://localhost:8000/api/v2/prototype/catalog/cvs/3001"
```

## Normal Search

```bash
curl "http://localhost:8000/api/jobs?q=marketing&industry=marketing&page=1&limit=10"
curl "http://localhost:8000/api/cvs?q=sales&skills=communication&page=1&limit=10"
curl "http://localhost:8000/api/candidates?desiredIndustry=human_resources"
```

Normal search returns `{items,total,page,limit,totalPages}` and does not return
matching percentages.

## Catalog Search

```bash
curl -X POST "http://localhost:8000/api/v2/prototype/catalog/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{"q":"backend devops"}'

curl -X POST "http://localhost:8000/api/v2/prototype/catalog/cvs/search" \
  -H "Content-Type: application/json" \
  -d '{"q":"python kubernetes","seniority":"senior"}'
```

## Run Matching

```bash
curl -X POST "http://localhost:8000/api/v2/prototype/matching/job/4001/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":5,"min_score":0.7}'

curl -X POST "http://localhost:8000/api/v2/prototype/matching/cv/3001/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":5,"min_score":0.7}'
```
