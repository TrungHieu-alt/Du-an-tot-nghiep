import tempfile
import unittest
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
        "department": "Growth",
        "location": {"city": "Hà Nội", "country": "VN", "remote_type": "hybrid"},
        "employment_type": ["fulltime"],
        "seniority": "manager",
        "team_size": 8,
        "description": "Own brand and demand generation.",
        "responsibilities": ["Lead campaigns"],
        "requirements": ["Excel", "Communication"],
        "nice_to_have": [],
        "skills": [{"name": "Excel", "level": "advanced"}],
        "experience_years": 5,
        "education_level": "bachelor",
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
        "target_role": "Sales Manager",
        "employment_type": ["fulltime"],
        "salary_expectation": "Negotiable",
        "availability": "immediately",
        "skills": [{"name": "Communication", "level": "advanced"}],
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

    def test_create_job_defaults_to_public_published_searchable_state(self):
        conn, cur = _make_conn([_job_row()])
        self._override_conn(conn)

        res = self.client.post("/api/job", json={"title": "Public by default"})

        self.assertEqual(res.status_code, 201)
        insert_params = cur.executed[0][1]
        self.assertEqual(
            insert_params[job_router.INSERTABLE_JOB_COLUMNS.index("status")],
            "published",
        )
        self.assertEqual(
            insert_params[job_router.INSERTABLE_JOB_COLUMNS.index("visibility")],
            "public",
        )
        self.assertFalse(insert_params[job_router.INSERTABLE_JOB_COLUMNS.index("archived")])

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
            "published",
        )
        self.assertEqual(
            insert_params[cv_router.INSERTABLE_CV_COLUMNS.index("visibility")],
            "public",
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
        self.assertIsNone(body["cv"]["file"])
        self.assertIn("warnings", body)

    def test_extract_pdf_preview_rejects_non_pdf(self):
        res = self.client.post(
            "/api/cvs/extract-pdf",
            files={"file": ("cv.txt", BytesIO(b"hello"), "text/plain")},
        )

        self.assertEqual(res.status_code, 400)

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
        self.assertEqual(cur.executed[0][1][cv_router.INSERTABLE_CV_COLUMNS.index("status")], "published")
        self.assertEqual(cur.executed[0][1][cv_router.INSERTABLE_CV_COLUMNS.index("visibility")], "public")
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
        self.assertIn("/api/job/my", paths)
        self.assertIn("/api/job/search", paths)
        self.assertIn("/api/job/{job_id}", paths)
        self.assertIn("/api/cv", paths)
        self.assertIn("/api/cv/my", paths)
        self.assertIn("/api/cv/upload", paths)
        self.assertIn("/api/cv/{cv_id}", paths)
        self.assertIn("/api/jobs", paths)
        self.assertIn("/api/cvs", paths)
        self.assertIn("/api/candidates", paths)


if __name__ == "__main__":
    unittest.main()
