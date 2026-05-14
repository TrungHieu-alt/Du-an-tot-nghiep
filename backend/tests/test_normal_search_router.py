import tempfile
import unittest
import json
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import cv_router, job_router, normal_search_router
from routers.auth import AuthUser, create_access_token


USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"
JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
NOW = datetime(2026, 5, 13, tzinfo=timezone.utc)


class _StubCursor:
    def __init__(self, responses):
        self._responses = list(responses)
        self.executed: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, tuple(params)))

    def fetchone(self):
        return self._responses.pop(0)

    def fetchall(self):
        return self._responses.pop(0)


class _StubConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _make_conn(responses):
    cur = _StubCursor(responses)
    return _StubConnection(cur), cur


def _json_payload(value):
    for attr in ("obj", "_obj", "wrapped", "_wrapped"):
        if hasattr(value, attr):
            return getattr(value, attr)
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _is_json_wrapper(value):
    return any(hasattr(value, attr) for attr in ("obj", "_obj", "wrapped", "_wrapped"))


def _job_row(**overrides):
    data = {
        "id": JOB_ID,
        "created_by": USER_ID,
        "company_id": "acme",
        "title": "Marketing Manager",
        "slug": "marketing-manager",
        "status": "published",
        "visibility": "public",
        "company_name": "Acme",
        "company_logo_url": None,
        "company_website": None,
        "company_location": "Hà Nội",
        "company_size": "100-500",
        "company_industry": "Marketing",
        "industry": "marketing",
        "occupation_group": "digital_marketing",
        "department": "Growth",
        "location": {"city": "Hà Nội", "country": "VN", "remote_type": "hybrid"},
        "employment_type": ["fulltime"],
        "seniority": "manager",
        "team_size": 8,
        "description": "Own brand and demand generation.",
        "responsibilities": ["Lead campaigns"],
        "requirements": ["Excel", "Communication"],
        "nice_to_have": [],
        "skills": [{"name": "Excel", "normalized_name": "excel", "level": "advanced", "category": "tool"}],
        "must_have_skills": [],
        "nice_to_have_skills": [],
        "tools_and_technologies": ["excel"],
        "domain_knowledge": ["brand"],
        "experience_years": 5,
        "education_level": "bachelor",
        "required_education": {"level": "bachelor", "major": "Marketing"},
        "required_certifications": [],
        "salary": {"min": 20000000, "max": 35000000, "currency": "VND"},
        "benefits": ["Insurance"],
        "bonus": None,
        "equity": None,
        "apply_url": None,
        "apply_email": None,
        "recruiter": {"name": "HR"},
        "how_to_apply": None,
        "application_deadline": None,
        "tags": ["brand"],
        "categories": ["Marketing"],
        "remote": False,
        "views": 0,
        "applications_count": 0,
        "pre_screen_questions": [],
        "required_docs": [],
        "published_by": None,
        "approved_at": None,
        "approved_by": None,
        "archived": False,
        "version": 1,
        "embedding": {},
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return tuple(data[column] for column in job_router.JOB_COLUMNS)


def _cv_row(**overrides):
    data = {
        "id": CV_ID,
        "created_by": USER_ID,
        "avatar_url": None,
        "fullname": "Nguyen Van A",
        "preferred_name": None,
        "email": "a@example.com",
        "phone": None,
        "location": {"city": "TP. Hồ Chí Minh", "country": "VN", "remote_type": "remote"},
        "headline": "Sales candidate",
        "summary": "B2B sales and customer service.",
        "industry": "sales",
        "occupation_group": "sales_executive",
        "career_level": "manager",
        "years_of_experience": 5,
        "target_role": "Sales Manager",
        "employment_type": ["fulltime"],
        "salary_expectation": "Negotiable",
        "availability": "immediately",
        "skills": [{"name": "Communication", "normalized_name": "communication", "level": "advanced", "category": "soft_skill"}],
        "tools_and_technologies": ["excel"],
        "domain_knowledge": ["sales"],
        "experiences": [{"title": "Sales Lead", "responsibilities": ["Lead sales"]}],
        "education": [{"degree": "Bachelor"}],
        "projects": [],
        "certifications": [{"name": "Sales Certificate"}],
        "languages": [],
        "portfolio": [],
        "references": [],
        "status": "published",
        "visibility": "public",
        "tags": ["sales"],
        "version": 1,
        "file": {},
        "archived": False,
        "embedding": {},
        "created_at": NOW,
        "updated_at": NOW,
    }
    data.update(overrides)
    return tuple(data[column] for column in cv_router.CV_COLUMNS)


class NormalJobCvRouterTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(job_router.router, prefix="/api")
        app.include_router(job_router.employer_requests_router, prefix="/api")
        app.include_router(cv_router.router, prefix="/api")
        app.include_router(cv_router.cvs_router, prefix="/api")
        app.include_router(normal_search_router.router, prefix="/api")
        self.user = AuthUser(
            id=USER_ID,
            email="user@example.com",
            full_name="User",
            role="candidate",
        )
        app.dependency_overrides[job_router.get_current_user] = lambda: self.user
        app.dependency_overrides[cv_router.get_current_user] = lambda: self.user
        self.app = app
        self.client = TestClient(app)

    def _override_conn(self, conn):
        self.app.dependency_overrides[job_router.get_db_connection] = lambda: conn
        self.app.dependency_overrides[cv_router.get_db_connection] = lambda: conn
        self.app.dependency_overrides[normal_search_router.get_db_connection] = lambda: conn

    def test_user_can_create_multiple_jobs_and_created_by_is_authenticated_user(self):
        conn, cur = _make_conn([_job_row(), _job_row(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaab")])
        self._override_conn(conn)

        for title in ("Marketing Manager", "Sales Lead"):
            res = self.client.post(
                "/api/job",
                json={
                    "title": title,
                    "status": "published",
                    "visibility": "public",
                    "company_industry": "Marketing",
                },
            )
            self.assertEqual(res.status_code, 201)
            self.assertEqual(res.json()["created_by"], USER_ID)

        insert_params = cur.executed[0][1]
        self.assertEqual(insert_params[0], USER_ID)
        self.assertEqual(len(cur.executed), 2)

    def test_employer_request_alias_returns_camel_case_and_uses_authenticated_user(self):
        conn, cur = _make_conn([_job_row()])
        self._override_conn(conn)

        res = self.client.post(
            "/api/employer/requests",
            json={
                "title": "Rich request",
                "companyName": "Acme",
                "companyIndustry": "Marketing",
                "location": {"city": "Hà Nội", "remoteType": "hybrid"},
                "employmentType": ["fulltime"],
                "preScreenQuestions": [{"q": "Years?", "required": True}],
            },
        )

        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body["createdBy"], USER_ID)
        self.assertEqual(body["companyName"], "Acme")
        insert_params = cur.executed[0][1]
        self.assertEqual(insert_params[0], USER_ID)
        self.assertEqual(
            insert_params[job_router.INSERTABLE_JOB_COLUMNS.index("company_name")],
            "Acme",
        )

    def test_create_job_defaults_to_draft_private_state(self):
        conn, cur = _make_conn([_job_row()])
        self._override_conn(conn)

        res = self.client.post("/api/job", json={"title": "Draft by default"})

        self.assertEqual(res.status_code, 201)
        insert_params = cur.executed[0][1]
        self.assertEqual(
            insert_params[job_router.INSERTABLE_JOB_COLUMNS.index("status")],
            "draft",
        )
        self.assertEqual(
            insert_params[job_router.INSERTABLE_JOB_COLUMNS.index("visibility")],
            "private",
        )
        self.assertFalse(insert_params[job_router.INSERTABLE_JOB_COLUMNS.index("archived")])

    def test_create_job_normalizes_enum_like_fields_before_insert(self):
        conn, cur = _make_conn([_job_row()])
        self._override_conn(conn)

        res = self.client.post(
            "/api/job",
            json={
                "title": "Senior React Developer",
                "status": "Published",
                "visibility": "Internal",
                "industry": "Information Technology",
                "occupation_group": "Software Engineering",
                "location": {"city": "Hà Nội", "remote_type": "work from home"},
                "employment_type": ["Full-time", "fulltime", "unsupported"],
                "seniority": "Senior Developer",
                "skills": [{"name": "ReactJS", "level": "Good", "category": "Technical Skill"}],
                "salary": {"currency": "Vietnamese Dong", "period": "Per Month"},
                "pre_screen_questions": [{"q": "Why?", "type": "short answer"}],
            },
        )

        self.assertEqual(res.status_code, 201)
        params = cur.executed[0][1]
        self.assertEqual(params[job_router.INSERTABLE_JOB_COLUMNS.index("status")], "published")
        self.assertEqual(params[job_router.INSERTABLE_JOB_COLUMNS.index("visibility")], "private")
        self.assertEqual(params[job_router.INSERTABLE_JOB_COLUMNS.index("industry")], "information_technology")
        self.assertEqual(params[job_router.INSERTABLE_JOB_COLUMNS.index("occupation_group")], "software_engineering")
        self.assertEqual(params[job_router.INSERTABLE_JOB_COLUMNS.index("employment_type")], ["fulltime"])
        self.assertEqual(params[job_router.INSERTABLE_JOB_COLUMNS.index("seniority")], "senior")
        location = _json_payload(params[job_router.INSERTABLE_JOB_COLUMNS.index("location")])
        self.assertEqual(location["remote_type"], "remote")
        skills = _json_payload(params[job_router.INSERTABLE_JOB_COLUMNS.index("skills")])
        self.assertEqual(skills[0]["normalized_name"], "react")
        self.assertEqual(skills[0]["level"], "intermediate")
        self.assertEqual(skills[0]["category"], "technical")
        salary = _json_payload(params[job_router.INSERTABLE_JOB_COLUMNS.index("salary")])
        self.assertEqual(salary["currency"], "VND")
        self.assertEqual(salary["period"], "month")
        questions = _json_payload(params[job_router.INSERTABLE_JOB_COLUMNS.index("pre_screen_questions")])
        self.assertEqual(questions[0]["type"], "text")

    def test_update_job_normalizes_enum_like_fields_before_update(self):
        conn, cur = _make_conn([_job_row(), _job_row()])
        self._override_conn(conn)

        res = self.client.patch(
            f"/api/job/{JOB_ID}",
            json={
                "visibility": "Visible",
                "seniority": "Engineering Manager",
                "education_level": "Đại học",
                "salary": {"currency": "usd", "period": "yearly"},
            },
        )

        self.assertEqual(res.status_code, 200)
        update_params = cur.executed[1][1]
        update_sql = cur.executed[1][0]
        self.assertIn("visibility", update_sql)
        self.assertIn("seniority", update_sql)
        self.assertIn("education_level", update_sql)
        self.assertIn("salary", update_sql)
        self.assertIn("public", update_params)
        self.assertIn("manager", update_params)
        self.assertIn("bachelor", update_params)
        salary = next(_json_payload(param) for param in update_params if _is_json_wrapper(param))
        self.assertEqual(salary["currency"], "USD")
        self.assertEqual(salary["period"], "year")

    def test_user_can_create_multiple_cvs_and_created_by_is_authenticated_user(self):
        conn, cur = _make_conn([_cv_row(), _cv_row(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbc")])
        self._override_conn(conn)

        for fullname in ("Nguyen Van A", "Tran Thi B"):
            res = self.client.post(
                "/api/cv",
                json={
                    "fullname": fullname,
                    "target_role": "Sales Manager",
                    "skills": [{"name": "Communication"}],
                },
            )
            self.assertEqual(res.status_code, 201)
            self.assertEqual(res.json()["created_by"], USER_ID)

        insert_params = cur.executed[0][1]
        self.assertEqual(insert_params[0], USER_ID)
        self.assertEqual(
            insert_params[cv_router.INSERTABLE_CV_COLUMNS.index("status")],
            "draft",
        )
        self.assertEqual(
            insert_params[cv_router.INSERTABLE_CV_COLUMNS.index("visibility")],
            "private",
        )
        self.assertFalse(insert_params[cv_router.INSERTABLE_CV_COLUMNS.index("archived")])
        self.assertEqual(len(cur.executed), 2)

    def test_cvs_alias_returns_camel_case_and_uses_authenticated_user(self):
        conn, cur = _make_conn([_cv_row()])
        self._override_conn(conn)

        res = self.client.post(
            "/api/cvs",
            json={
                "fullname": "Nguyen Van A",
                "preferredName": "A",
                "targetRole": "Sales Manager",
                "employmentType": ["fulltime"],
                "skills": [{"name": "Communication", "years": 3}],
            },
        )

        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body["createdBy"], USER_ID)
        self.assertEqual(body["targetRole"], "Sales Manager")
        insert_params = cur.executed[0][1]
        self.assertEqual(insert_params[0], USER_ID)
        self.assertEqual(
            insert_params[cv_router.INSERTABLE_CV_COLUMNS.index("target_role")],
            "Sales Manager",
        )

    def test_create_cv_normalizes_enum_like_fields_before_insert(self):
        conn, cur = _make_conn([_cv_row()])
        self._override_conn(conn)

        res = self.client.post(
            "/api/cv",
            json={
                "fullname": "Nguyen Van A",
                "industry": "Information Technology",
                "occupation_group": "Software Engineering",
                "career_level": "Senior Developer",
                "employment_type": ["Full-time", "fulltime", "bad value"],
                "skills": [{"name": "ReactJS", "level": "Good", "category": "Technical Skill"}],
                "education": [{"degree": "Đại học", "level": "Đại học", "school": "Demo"}],
                "languages": [{"name": "English", "level": "B1"}],
                "portfolio": [{"media_type": "GitHub", "url": "https://github.com/demo"}],
                "status": "Published",
                "visibility": "Internal",
            },
        )

        self.assertEqual(res.status_code, 201)
        params = cur.executed[0][1]
        self.assertEqual(params[cv_router.INSERTABLE_CV_COLUMNS.index("industry")], "information_technology")
        self.assertEqual(params[cv_router.INSERTABLE_CV_COLUMNS.index("occupation_group")], "software_engineering")
        self.assertEqual(params[cv_router.INSERTABLE_CV_COLUMNS.index("career_level")], "senior")
        self.assertEqual(params[cv_router.INSERTABLE_CV_COLUMNS.index("employment_type")], ["fulltime"])
        self.assertEqual(params[cv_router.INSERTABLE_CV_COLUMNS.index("status")], "published")
        self.assertEqual(params[cv_router.INSERTABLE_CV_COLUMNS.index("visibility")], "private")
        skills = _json_payload(params[cv_router.INSERTABLE_CV_COLUMNS.index("skills")])
        self.assertEqual(skills[0]["normalized_name"], "react")
        self.assertEqual(skills[0]["level"], "intermediate")
        education = _json_payload(params[cv_router.INSERTABLE_CV_COLUMNS.index("education")])
        self.assertEqual(education[0]["level"], "bachelor")
        languages = _json_payload(params[cv_router.INSERTABLE_CV_COLUMNS.index("languages")])
        self.assertEqual(languages[0]["level"], "intermediate")
        portfolio = _json_payload(params[cv_router.INSERTABLE_CV_COLUMNS.index("portfolio")])
        self.assertEqual(portfolio[0]["media_type"], "github")

    def test_update_cv_normalizes_enum_like_fields_before_update(self):
        conn, cur = _make_conn([_cv_row(), _cv_row()])
        self._override_conn(conn)

        res = self.client.patch(
            f"/api/cv/{CV_ID}",
            json={
                "career_level": "2-4 years experience",
                "employment_type": ["Part-time"],
                "languages": [{"name": "English", "level": "C1"}],
            },
        )

        self.assertEqual(res.status_code, 200)
        update_params = cur.executed[1][1]
        self.assertIn("middle", update_params)
        self.assertIn(["parttime"], update_params)
        languages = next(_json_payload(param) for param in update_params if _is_json_wrapper(param))
        self.assertEqual(languages[0]["level"], "proficient")

    def test_extract_pdf_preview_returns_draft_cv_without_saving(self):
        original_extractor = cv_router._extract_pdf_text
        cv_router._extract_pdf_text = lambda content: (
            "\n".join(
                [
                    "Nguyen Van A",
                    "Frontend Developer",
                    "a@example.com",
                    "Skills",
                    "React, TypeScript",
                    "Experience",
                    "Frontend Intern at Demo Co",
                    "Education",
                    "Bachelor - Demo University",
                ]
            ),
            ["Docling unavailable or failed; used local test fallback."],
        )
        try:
            res = self.client.post(
                "/api/cvs/extract-pdf",
                files={"file": ("cv.pdf", BytesIO(b"%PDF-1.4\nbody"), "application/pdf")},
            )
        finally:
            cv_router._extract_pdf_text = original_extractor

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("Nguyen Van A", body["extractedText"])
        self.assertEqual(body["cv"]["fullname"], "Nguyen Van A")
        self.assertEqual(body["cv"]["email"], "a@example.com")
        self.assertEqual(body["cv"]["status"], "draft")
        self.assertEqual(body["cv"]["careerLevel"], "intern")
        self.assertEqual(body["cv"]["file"]["mimetype"], "application/pdf")
        self.assertIn("warnings", body)

    def test_extract_pdf_preview_rejects_non_pdf(self):
        res = self.client.post(
            "/api/cvs/extract-pdf",
            files={"file": ("cv.txt", BytesIO(b"hello"), "text/plain")},
        )

        self.assertEqual(res.status_code, 400)

    def test_extract_job_text_returns_normalized_multi_industry_job(self):
        conn, _ = _make_conn([])
        self._override_conn(conn)

        res = self.client.post(
            "/api/job/extract",
            json={
                "text": (
                    "Senior React Developer\n"
                    "Good knowledge of React, strong experience with Python. "
                    "Looking for full-time hybrid role. Graduated from university."
                )
            },
        )

        self.assertEqual(res.status_code, 200)
        job = res.json()["job"]
        self.assertEqual(job["status"], "draft")
        self.assertEqual(job["visibility"], "private")
        self.assertEqual(job["seniority"], "senior")
        self.assertEqual(job["employmentType"], ["fulltime"])
        self.assertEqual(job["location"]["remoteType"], "hybrid")
        self.assertEqual(job["educationLevel"], "bachelor")
        self.assertEqual(job["skills"][0]["normalizedName"], "react")
        self.assertEqual(job["skills"][0]["level"], "intermediate")

    def test_created_by_from_client_body_is_rejected(self):
        conn, _ = _make_conn([])
        self._override_conn(conn)

        res = self.client.post(
            "/api/job",
            json={"title": "Bad", "created_by": OTHER_USER_ID},
        )

        self.assertEqual(res.status_code, 422)

    def test_user_cannot_update_another_users_job(self):
        conn, _ = _make_conn([_job_row(created_by=OTHER_USER_ID)])
        self._override_conn(conn)

        res = self.client.patch(f"/api/job/{JOB_ID}", json={"title": "Updated"})

        self.assertEqual(res.status_code, 404)
        self.assertFalse(conn.committed)

    def test_user_cannot_delete_another_users_cv(self):
        conn, _ = _make_conn([_cv_row(created_by=OTHER_USER_ID)])
        self._override_conn(conn)

        res = self.client.delete(f"/api/cv/{CV_ID}")

        self.assertEqual(res.status_code, 404)
        self.assertFalse(conn.committed)

    def test_pdf_upload_accepts_only_pdf_and_stores_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            cv_router.UPLOAD_DIR = Path(tmp)
            conn, cur = _make_conn([
                _cv_row(file={"filename": "tmp.pdf"}),
                _cv_row(file={"filename": "tmp.pdf", "uploaded_at": NOW.isoformat()}),
            ])
            self._override_conn(conn)

            res = self.client.post(
                "/api/cv/upload",
                files={"file": ("resume.pdf", b"%PDF-1.4\ncontent", "application/pdf")},
                data={"fullname": "Uploaded Candidate"},
            )

        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body["created_by"], USER_ID)
        self.assertEqual(body["file"]["uploaded_at"], NOW.isoformat())
        self.assertEqual(cur.executed[0][1][cv_router.INSERTABLE_CV_COLUMNS.index("status")], "draft")
        self.assertEqual(cur.executed[0][1][cv_router.INSERTABLE_CV_COLUMNS.index("visibility")], "private")
        self.assertFalse(cur.executed[0][1][cv_router.INSERTABLE_CV_COLUMNS.index("archived")])
        self.assertIn("UPDATE cvs", cur.executed[1][0])

    def test_pdf_upload_rejects_non_pdf(self):
        conn, _ = _make_conn([])
        self._override_conn(conn)

        res = self.client.post(
            "/api/cv/upload",
            files={"file": ("resume.txt", b"hello", "text/plain")},
        )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["detail"], "Only PDF files are accepted")

    def test_public_job_search_uses_normal_jobs_table_and_filters_public_visibility(self):
        conn, cur = _make_conn(
            [
                [
                    _job_row(),
                    _job_row(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaab", status="draft"),
                    _job_row(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaac", visibility="private"),
                    _job_row(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaad", status="closed"),
                    _job_row(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaae", archived=True),
                ]
            ]
        )
        self._override_conn(conn)

        res = self.client.get(
            "/api/job/search",
            params={"keyword": "marketing", "company_industry": "Marketing"},
        )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["company_industry"], "Marketing")
        sql = cur.executed[0][0]
        self.assertIn("FROM jobs", sql)
        self.assertIn("status = 'published'", sql)
        self.assertIn("visibility = 'public'", sql)
        self.assertIn("archived = false", sql)
        self.assertNotIn("job_posts_v2", sql)
        forbidden = {
            "totalScore",
            "matchScore",
            "matchLevel",
            "scores",
            "strengths",
            "weaknesses",
            "recommendation",
            "matchedSkills",
            "missingMustHaveSkills",
            "missingNiceToHaveSkills",
        }
        self.assertTrue(forbidden.isdisjoint(body["items"][0]))
        self.assertEqual(body["pagination"]["total"], 1)

    def test_public_job_search_with_no_query_returns_public_published_jobs(self):
        conn, _ = _make_conn([[_job_row(), _job_row(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaf", status="draft")]])
        self._override_conn(conn)

        res = self.client.get("/api/job/search")

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["id"], JOB_ID)

    def test_public_job_search_accepts_snake_case_employment_type_filter(self):
        conn, _ = _make_conn([[_job_row()]])
        self._override_conn(conn)

        res = self.client.get("/api/job/search", params={"employment_type": "fulltime"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)

    def test_public_job_search_filters_use_normalized_enum_keys(self):
        conn, _ = _make_conn([[_job_row()]])
        self._override_conn(conn)

        res = self.client.get(
            "/api/job/search",
            params={
                "industry": "Marketing",
                "occupationGroup": "Digital Marketing",
                "employmentType": "Full-time",
                "remote_type": "2 days office, 3 days remote",
                "seniority": "Engineering Manager",
                "educationLevel": "University",
                "salary.currency": "Vietnamese Dong",
            },
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)

    def test_public_cv_search_with_no_query_returns_public_published_cvs(self):
        conn, cur = _make_conn(
            [
                [
                    _cv_row(),
                    _cv_row(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbc1", status="draft"),
                    _cv_row(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbc2", visibility="private"),
                    _cv_row(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbc3", archived=True),
                ]
            ]
        )
        self._override_conn(conn)

        res = self.client.get("/api/cv/search")

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["id"], CV_ID)
        sql = cur.executed[0][0]
        self.assertIn("FROM cvs", sql)
        self.assertIn("status = 'published'", sql)
        self.assertIn("visibility = 'public'", sql)
        self.assertIn("archived = false", sql)
        self.assertNotIn("candidate_profiles_v2", sql)
        forbidden = {
            "totalScore",
            "matchScore",
            "matchLevel",
            "scores",
            "strengths",
            "weaknesses",
            "recommendation",
            "matchedSkills",
            "missingMustHaveSkills",
            "missingNiceToHaveSkills",
        }
        self.assertTrue(forbidden.isdisjoint(body["items"][0]))
        self.assertEqual(body["pagination"]["total"], 1)

    def test_public_cv_search_filters_use_normalized_enum_keys(self):
        conn, _ = _make_conn([
            [
                _cv_row(
                    education=[{"degree": "Bachelor", "level": "bachelor", "major": "Sales"}],
                    languages=[{"name": "English", "level": "intermediate"}],
                )
            ]
        ])
        self._override_conn(conn)

        res = self.client.get(
            "/api/cv/search",
            params={
                "industry": "Sales",
                "occupationGroup": "Sales Executive",
                "careerLevel": "Engineering Manager",
                "employmentType": "Full-time",
                "educationLevel": "University",
                "languageName": "English",
                "languageLevel": "B1",
            },
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)

    def test_public_cv_search_filters_by_skills_and_target_role(self):
        conn, _ = _make_conn(
            [
                [
                    _cv_row(
                        target_role="Frontend Developer",
                        skills=[{"name": "React"}, {"name": "TypeScript"}],
                    ),
                    _cv_row(
                        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbc4",
                        target_role="Accountant",
                        skills=[{"name": "Excel"}],
                    ),
                ]
            ]
        )
        self._override_conn(conn)

        res = self.client.get(
            "/api/cv/search",
            params={"skills": "React", "target_role": "Frontend"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)
        self.assertEqual(res.json()["items"][0]["target_role"], "Frontend Developer")

    def test_public_cv_search_keyword_includes_language_names(self):
        conn, _ = _make_conn(
            [
                [
                    _cv_row(languages=[{"name": "Japanese", "level": "intermediate"}]),
                    _cv_row(
                        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbc5",
                        languages=[{"name": "English", "level": "intermediate"}],
                    ),
                ]
            ]
        )
        self._override_conn(conn)

        res = self.client.get("/api/cv/search", params={"q": "Japanese"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)
        self.assertEqual(res.json()["items"][0]["id"], CV_ID)

    def test_public_cv_search_accepts_multi_industry_filter_aliases(self):
        conn, _ = _make_conn(
            [
                [
                    _cv_row(
                        industry="information_technology",
                        occupation_group="software_engineering",
                        career_level="middle",
                        years_of_experience=3,
                        target_role="Backend Developer",
                        location={"city": "Hà Nội", "country": "Việt Nam"},
                        employment_type=["fulltime"],
                        skills=[{"name": "React", "normalized_name": "react"}],
                        tools_and_technologies=["FastAPI"],
                        domain_knowledge=["ecommerce"],
                        education=[{"level": "bachelor", "major": "Computer Science", "school": "Demo University"}],
                        certifications=[{"name": "AWS"}],
                        languages=[{"name": "English", "level": "intermediate"}],
                        tags=["backend"],
                    ),
                    _cv_row(
                        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbc6",
                        industry="sales",
                        occupation_group="sales_executive",
                        career_level="manager",
                        target_role="Sales Manager",
                        location={"city": "Đà Nẵng", "country": "Việt Nam"},
                        skills=[{"name": "Excel", "normalized_name": "excel"}],
                        education=[{"level": "associate", "major": "Sales"}],
                        languages=[{"name": "English", "level": "basic"}],
                    ),
                ]
            ]
        )
        self._override_conn(conn)

        res = self.client.get(
            "/api/cv/search",
            params={
                "industry": "information_technology",
                "occupationGroup": "software_engineering",
                "careerLevel": "junior,middle",
                "yearsOfExperienceMin": 1,
                "yearsOfExperienceMax": 4,
                "employmentType": "fulltime",
                "city": "Hà Nội",
                "locationCountry": "Việt Nam",
                "skills": "ReactJS",
                "toolsAndTechnologies": "fastapi",
                "domainKnowledge": "ecommerce",
                "educationLevel": "bachelor,master",
                "educationMajor": "Computer",
                "certifications.name": "AWS",
                "languages.name": "English",
                "languages.level": "B1",
                "tags": "backend",
            },
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)
        self.assertEqual(res.json()["items"][0]["target_role"], "Backend Developer")

    def test_public_cv_search_education_level_matches_legacy_degree_values(self):
        conn, _ = _make_conn(
            [
                [
                    _cv_row(
                        education=[{"degree": "Bachelor", "major": "Computer Science", "school": "Demo University"}],
                    ),
                    _cv_row(
                        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbc7",
                        education=[{"degree": "High School", "major": "General", "school": "Demo High School"}],
                    ),
                ]
            ]
        )
        self._override_conn(conn)

        res = self.client.get("/api/cv/search", params={"educationLevel": "bachelor"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)
        self.assertEqual(res.json()["items"][0]["id"], CV_ID)

    def test_unauthenticated_user_can_view_public_job_detail(self):
        conn, _ = _make_conn([_job_row()])
        self._override_conn(conn)

        res = self.client.get(f"/api/job/{JOB_ID}")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], JOB_ID)

    def test_unauthenticated_user_cannot_view_private_or_draft_job_detail(self):
        conn, _ = _make_conn([_job_row(status="draft", visibility="private")])
        self._override_conn(conn)

        res = self.client.get(f"/api/job/{JOB_ID}")

        self.assertEqual(res.status_code, 404)

    def test_authenticated_owner_can_view_own_draft_private_job_detail(self):
        token = create_access_token(self.user)
        conn, _ = _make_conn(
            [
                _job_row(status="draft", visibility="private"),
                (USER_ID, "user@example.com", "User", "candidate"),
            ]
        )
        self._override_conn(conn)

        res = self.client.get(
            f"/api/job/{JOB_ID}",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "draft")

    def test_unauthenticated_user_can_view_public_cv_detail(self):
        conn, _ = _make_conn([_cv_row()])
        self._override_conn(conn)

        res = self.client.get(f"/api/cv/{CV_ID}")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], CV_ID)

    def test_unauthenticated_user_cannot_view_private_or_draft_cv_detail(self):
        conn, _ = _make_conn([_cv_row(status="draft", visibility="private")])
        self._override_conn(conn)

        res = self.client.get(f"/api/cv/{CV_ID}")

        self.assertEqual(res.status_code, 404)

    def test_authenticated_owner_can_view_own_draft_private_cv_detail(self):
        token = create_access_token(self.user)
        conn, _ = _make_conn(
            [
                _cv_row(status="draft", visibility="private"),
                (USER_ID, "user@example.com", "User", "candidate"),
            ]
        )
        self._override_conn(conn)

        res = self.client.get(
            f"/api/cv/{CV_ID}",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "draft")

    def test_job_write_and_my_endpoints_still_require_authentication(self):
        app = FastAPI()
        app.include_router(job_router.router, prefix="/api")
        app.include_router(cv_router.router, prefix="/api")
        conn, _ = _make_conn([])
        app.dependency_overrides[job_router.get_db_connection] = lambda: conn
        app.dependency_overrides[cv_router.get_db_connection] = lambda: conn
        client = TestClient(app)

        self.assertEqual(client.post("/api/job", json={"title": "No auth"}).status_code, 401)
        self.assertEqual(client.get("/api/job/my").status_code, 401)
        self.assertEqual(client.patch(f"/api/job/{JOB_ID}", json={"title": "No auth"}).status_code, 401)
        self.assertEqual(client.delete(f"/api/job/{JOB_ID}").status_code, 401)
        self.assertEqual(client.post("/api/cv", json={"fullname": "No auth"}).status_code, 401)
        self.assertEqual(client.get("/api/cv/my").status_code, 401)
        self.assertEqual(client.patch(f"/api/cv/{CV_ID}", json={"fullname": "No auth"}).status_code, 401)
        self.assertEqual(client.delete(f"/api/cv/{CV_ID}").status_code, 401)
        self.assertEqual(
            client.post(
                "/api/cv/upload",
                files={"file": ("resume.pdf", b"%PDF-1.4\n", "application/pdf")},
            ).status_code,
            401,
        )

    def test_normal_search_aliases_do_not_use_v2_data(self):
        conn, cur = _make_conn([[_job_row()]])
        self._override_conn(conn)

        res = self.client.get("/api/jobs", params={"q": "excel"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)
        self.assertIn("FROM jobs", cur.executed[0][0])
        self.assertNotIn("job_posts_v2", cur.executed[0][0])

    def test_cv_search_alias_uses_normal_cvs_table(self):
        conn, cur = _make_conn([[_cv_row()]])
        self._override_conn(conn)

        res = self.client.get("/api/candidates", params={"q": "sales"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["total"], 1)
        self.assertIn("FROM cvs", cur.executed[0][0])
        self.assertNotIn("candidate_profiles_v2", cur.executed[0][0])

    def test_openapi_contains_normal_job_cv_paths_and_existing_v2_paths(self):
        schema = self.client.get("/openapi.json").json()
        paths = set(schema["paths"])

        self.assertIn("/api/job", paths)
        self.assertIn("/api/job/extract", paths)
        self.assertIn("/api/job/my", paths)
        self.assertIn("/api/job/search", paths)
        self.assertIn("/api/job/{job_id}", paths)
        self.assertIn("/api/cv", paths)
        self.assertIn("/api/cv/my", paths)
        self.assertIn("/api/cv/upload", paths)
        self.assertIn("/api/cvs/extract-pdf", paths)
        self.assertIn("/api/cv/{cv_id}", paths)
        self.assertIn("/api/jobs", paths)
        self.assertIn("/api/cvs", paths)
        self.assertIn("/api/candidates", paths)


if __name__ == "__main__":
    unittest.main()
