# V2 API Examples

All ID fields are integers (`BIGINT` in PostgreSQL). Enum values must match the
backend constraints exactly:

- `location`: `Hà Nội`, `TP. Hồ Chí Minh`, `Đà Nẵng`
- `job_type`: `remote`, `fulltime`, `parttime`
- `seniority`: `intern`, `fresher`, `junior`, `mid`, `senior`, `lead`
- `education`: `high_school`, `bachelor`, `master`, `phd`

## Catalog Browse

```bash
curl "http://localhost:8000/api/v2/prototype/catalog/jobs?limit=10&offset=0"
curl "http://localhost:8000/api/v2/prototype/catalog/cvs?limit=10&offset=0"
curl "http://localhost:8000/api/v2/prototype/catalog/jobs/4001"
curl "http://localhost:8000/api/v2/prototype/catalog/cvs/3001"
```

## Normal Search

```bash
curl "http://localhost:8000/api/jobs?q=lap+trinh&industry=information_technology&page=1&limit=10"
curl "http://localhost:8000/api/cvs?q=ke+toan&skills=excel&page=1&limit=10"
curl "http://localhost:8000/api/candidates?desiredIndustry=human_resources"
curl "http://localhost:8000/api/cv/search?q=Python+FastAPI&industry=information_technology&occupationGroup=software_engineering&careerLevel=junior,middle&yearsOfExperienceMin=1&yearsOfExperienceMax=4&skills=python,fastapi&employmentType=fulltime&educationLevel=bachelor&languageLevel=intermediate&sort=yearsOfExperience_desc"
```

Normal search returns `{items,total,page,limit,totalPages}` and does not return
matching percentages.

## Normal Write -> V2 Preparation Sync

Normal CV/Job create and update requests do not require the frontend to send V2
data. The backend builds linked V2 preparation rows automatically:

- `cvs.id` -> `candidate_profiles_v2.normal_cv_id`
- `jobs.id` -> `job_posts_v2.normal_job_id`

V2 sync uses selected profile/JD fields only, preprocesses the generated text,
and stores `prepared_text`, `prepared_text_en`, `source_language`,
`preprocess_warnings`, `translation_warnings`, and `text_quality` on the V2
rows. Translation is V2-only and runs through `deep-translator` only when
`V2_TRANSLATION_ENABLED=true`; normal extraction remains translation-free.

Normal create/update payloads must not send `createdBy` or `embedding`.
`createdBy` is set from the authenticated user on the backend. Normal CV/Job
tables do not store embedding fields; embeddings stay in V2 embedding tables.

### Normal CV create payload

```json
{
  "avatarUrl": "string",
  "fullname": "Nguyễn Văn An",
  "preferredName": "An",
  "email": "an@example.com",
  "phone": "0900000000",
  "location": {
    "city": "Hà Nội",
    "state": "",
    "country": "Việt Nam",
    "remoteType": "onsite"
  },
  "headline": "Lập trình viên Backend Python",
  "summary": "Có kinh nghiệm xây dựng API với FastAPI và PostgreSQL.",
  "industry": "information_technology",
  "occupationGroup": "software_engineering",
  "careerLevel": "middle",
  "yearsOfExperience": 3,
  "targetRole": "Backend Developer",
  "employmentType": ["fulltime"],
  "salaryExpectation": "Thỏa thuận",
  "availability": "Có thể nhận việc sau 30 ngày",
  "skills": [
    {
      "name": "ReactJS",
      "normalizedName": "react",
      "level": "intermediate",
      "category": "technical",
      "years": 2
    }
  ],
  "toolsAndTechnologies": ["docker", "postgresql"],
  "domainKnowledge": ["recruitment"],
  "experiences": [
    {
      "id": "exp-1",
      "title": "Backend Developer",
      "company": "Công ty Công nghệ ABC",
      "companyWebsite": "https://example.com",
      "location": "Hà Nội",
      "from": "2024-01-01",
      "to": "2026-01-01",
      "isCurrent": false,
      "employmentType": "fulltime",
      "teamSize": 5,
      "responsibilities": ["Xây dựng REST API bằng FastAPI."],
      "achievements": ["Tối ưu thời gian phản hồi API."],
      "skillsUsed": ["python", "postgresql"],
      "toolsUsed": ["docker"],
      "tags": ["backend"]
    }
  ],
  "education": [
    {
      "degree": "Cử nhân",
      "level": "bachelor",
      "major": "Công nghệ thông tin",
      "school": "Đại học Bách Khoa",
      "from": "2019-09-01",
      "to": "2023-06-01",
      "gpa": "3.2/4.0"
    }
  ],
  "projects": [
    {
      "name": "Hệ thống tuyển dụng",
      "description": "Xây dựng backend cho hệ thống tuyển dụng.",
      "role": "Backend Developer",
      "from": "2025-01-01",
      "to": "2025-12-31",
      "tools": ["fastapi"],
      "skillsUsed": ["python"],
      "outcomes": ["Hoàn thiện API quản lý hồ sơ ứng viên."],
      "techStack": ["python", "postgresql"],
      "url": "https://example.com",
      "metrics": ["Giảm 30% thời gian xử lý."]
    }
  ],
  "certifications": [
    {
      "name": "AWS Certified Cloud Practitioner",
      "issuer": "AWS",
      "issueDate": "2025-01-01",
      "expiryDate": "2028-01-01",
      "credentialUrl": "https://example.com/cert"
    }
  ],
  "languages": [{ "name": "English", "level": "intermediate" }],
  "portfolio": [
    {
      "mediaType": "website",
      "url": "https://portfolio.example.com",
      "description": "Portfolio cá nhân"
    }
  ],
  "references": [
    {
      "name": "Người tham chiếu",
      "relation": "Quản lý trực tiếp",
      "contact": "ref@example.com",
      "note": "Liên hệ khi cần"
    }
  ],
  "status": "draft",
  "visibility": "private",
  "tags": ["backend"],
  "version": 1,
  "archived": false
}
```

### Normal Job create payload

```json
{
  "companyId": "company-1",
  "title": "Lập trình viên Backend Python",
  "slug": "lap-trinh-vien-backend-python",
  "status": "draft",
  "visibility": "private",
  "companyName": "Công ty Công nghệ ABC",
  "companyLogoUrl": "https://example.com/logo.png",
  "companyWebsite": "https://example.com",
  "companyLocation": "Hà Nội",
  "companySize": "50-100",
  "companyIndustry": "Công nghệ thông tin",
  "industry": "information_technology",
  "occupationGroup": "software_engineering",
  "department": "Engineering",
  "location": {
    "city": "Hà Nội",
    "state": "",
    "country": "Việt Nam",
    "remoteType": "onsite"
  },
  "employmentType": ["fulltime"],
  "seniority": "middle",
  "teamSize": 6,
  "description": "Tham gia phát triển hệ thống tuyển dụng.",
  "responsibilities": ["Xây dựng API bằng FastAPI."],
  "requirements": ["Có kinh nghiệm với Python và PostgreSQL."],
  "niceToHave": ["Biết Docker là lợi thế."],
  "skills": [
    {
      "name": "Python",
      "normalizedName": "python",
      "level": "advanced",
      "category": "technical"
    }
  ],
  "mustHaveSkills": [
    {
      "name": "FastAPI",
      "normalizedName": "fastapi",
      "level": "intermediate",
      "category": "technical",
      "weight": 10
    }
  ],
  "niceToHaveSkills": [
    {
      "name": "Docker",
      "normalizedName": "docker",
      "level": "beginner",
      "category": "tool",
      "weight": 5
    }
  ],
  "toolsAndTechnologies": ["docker", "git"],
  "domainKnowledge": ["recruitment"],
  "experienceYears": 3,
  "educationLevel": "bachelor",
  "requiredEducation": {
    "level": "bachelor",
    "major": "Công nghệ thông tin"
  },
  "requiredCertifications": ["AWS"],
  "salary": {
    "min": 20000000,
    "max": 35000000,
    "currency": "VND",
    "period": "month"
  },
  "benefits": ["Bảo hiểm", "Lương tháng 13"],
  "bonus": "Theo hiệu quả công việc",
  "equity": "",
  "applyUrl": "https://example.com/apply",
  "applyEmail": "hr@example.com",
  "recruiter": {
    "name": "Nguyễn Thị HR",
    "email": "hr@example.com",
    "phone": "0900000001"
  },
  "howToApply": "Ứng tuyển qua hệ thống.",
  "applicationDeadline": "2026-12-31",
  "tags": ["backend"],
  "categories": ["engineering"],
  "remote": false,
  "preScreenQuestions": [
    {
      "q": "Bạn có kinh nghiệm FastAPI bao lâu?",
      "type": "text",
      "required": true,
      "options": []
    }
  ],
  "requiredDocs": ["cv"],
  "archived": false,
  "version": 1
}
```

Normal CV/Job responses add backend-owned system fields:

```json
{
  "id": "uuid",
  "createdBy": "authenticated-user-id",
  "visibility": "private",
  "archived": false,
  "createdAt": "2026-05-15T00:00:00.000Z",
  "updatedAt": "2026-05-15T00:00:00.000Z"
}
```

Normal Job responses can also include backend-owned counters/approval metadata:

```json
{
  "views": 0,
  "applicationsCount": 0,
  "publishedBy": null,
  "approvedAt": null,
  "approvedBy": null
}
```

## Normal Extraction

```bash
curl -X POST "http://localhost:8000/api/job/extract" \
  -H "Authorization: Bearer <recruiter-token>" \
  -H "Content-Type: application/json" \
  -d '{"text":"Lập trình viên Backend Python\nKỹ năng: Python, FastAPI, PostgreSQL"}'

curl -X POST "http://localhost:8000/api/cvs/extract-pdf" \
  -H "Authorization: Bearer <candidate-token>" \
  -F "file=@/path/to/cv.pdf"
```

Normal extraction preprocesses local extracted text before parsing. Responses
include `rawTextLength`, `cleanTextLength`, `preprocessWarnings`,
`textQuality`, and `cleanedText`; they do not include matching scores or
recommendations.

## Normal Applications

```bash
curl -X POST "http://localhost:8000/api/applications" \
  -H "Authorization: Bearer <candidate-token>" \
  -H "Content-Type: application/json" \
  -d '{"jobId":"<job-uuid>","cvId":"<cv-uuid>","coverLetter":"I can start next month."}'

curl "http://localhost:8000/api/applications/me" \
  -H "Authorization: Bearer <candidate-token>"

curl "http://localhost:8000/api/job/<job-uuid>/applications" \
  -H "Authorization: Bearer <recruiter-token>"

curl -X PATCH "http://localhost:8000/api/applications/<application-uuid>/status" \
  -H "Authorization: Bearer <recruiter-token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"reviewing"}'
```

Normal application responses connect `jobId`, `cvId`, `candidateId`, and
`recruiterId`; they do not include matching scores or recommendations.

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
