import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

NORMAL_RUNTIME_FILES = [
    REPO_ROOT / "backend" / "main.py",
    REPO_ROOT / "backend" / "routers" / "job_router.py",
    REPO_ROOT / "backend" / "routers" / "cv_router.py",
    REPO_ROOT / "backend" / "routers" / "application_router.py",
    REPO_ROOT / "backend" / "routers" / "normal_search_router.py",
    REPO_ROOT / "backend" / "routers" / "auth.py",
    REPO_ROOT / "backend" / "schemas" / "normal_job_schema.py",
    REPO_ROOT / "backend" / "schemas" / "normal_cv_schema.py",
    REPO_ROOT / "backend" / "schemas" / "normal_application_schema.py",
    REPO_ROOT / "frontend" / "src" / "api" / "normal.ts",
    REPO_ROOT / "frontend" / "lib" / "api-routes.ts",
]

BACKEND_RUNTIME_ROOTS = [
    REPO_ROOT / "backend" / "main.py",
    REPO_ROOT / "backend" / "routers",
    REPO_ROOT / "backend" / "schemas",
    REPO_ROOT / "backend" / "matching_v2",
    REPO_ROOT / "backend" / "v2_search",
]

FORBIDDEN_NORMAL_TERMS = [
    r"\bmongodb\b",
    r"\bmongo\b",
    r"\bmongoose\b",
    r"@nestjs/mongoose",
    r"\bnestjs\b",
    r"@Schema\b",
    r"@Prop\b",
    r"\bSchemaFactory\b",
    r"\bMongooseSchema\b",
    r"\bObjectId\b",
    r"\bMONGO_URI\b",
    r"\bpymongo\b",
    r"\bmotor\b",
    r"\binsertOne\b",
    r"\bfindOne\b",
    r"\bupdateOne\b",
    r"\bdeleteOne\b",
    r"\bMongoClient\b",
]

FORBIDDEN_CLIENT_IMPORTS = [
    r"\bpymongo\b",
    r"\bmotor\b",
    r"\bMongoClient\b",
    r"\bmongoose\b",
    r"@nestjs/mongoose",
    r"\bSchemaFactory\b",
    r"\bObjectId\b",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _existing(paths: list[Path]) -> list[Path]:
    # Backend tests run inside the backend container where the repo-level
    # frontend and compose files may not be mounted. Scan them when available
    # from a full checkout, but keep the backend architecture guard portable.
    return [path for path in paths if path.exists()]


def _python_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


class PostgresOnlyArchitectureTests(unittest.TestCase):
    def test_active_normal_job_cv_search_files_have_no_mongo_nest_mongoose_terms(self):
        pattern = re.compile("|".join(FORBIDDEN_NORMAL_TERMS), re.IGNORECASE)
        offenders: list[str] = []

        for path in _existing(NORMAL_RUNTIME_FILES):
            text = _read(path)
            for match in pattern.finditer(text):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{match.group(0)}")

        self.assertEqual(offenders, [])

    def test_backend_runtime_imports_no_mongo_clients_or_nest_mongoose(self):
        pattern = re.compile("|".join(FORBIDDEN_CLIENT_IMPORTS), re.IGNORECASE)
        offenders: list[str] = []

        for root in BACKEND_RUNTIME_ROOTS:
            for path in _python_files(root):
                text = _read(path)
                for match in pattern.finditer(text):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{match.group(0)}")

        self.assertEqual(offenders, [])

    def test_compose_env_and_backend_dependencies_do_not_require_mongo(self):
        files = [
            REPO_ROOT / "docker-compose.yml",
            REPO_ROOT / ".env.example",
            REPO_ROOT / "backend" / "requirements.txt",
            REPO_ROOT / "frontend" / "package.json",
        ]
        pattern = re.compile(
            r"\bMONGO_URI\b|\bpymongo\b|\bmotor\b|\bmongoose\b|@nestjs/mongoose|mongo:",
            re.IGNORECASE,
        )
        offenders: list[str] = []

        for path in _existing(files):
            text = _read(path)
            for match in pattern.finditer(text):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{match.group(0)}")

        self.assertEqual(offenders, [])

    def test_normal_job_cv_runtime_targets_postgresql_tables_not_v2_or_scenario_data(self):
        job_text = _read(REPO_ROOT / "backend" / "routers" / "job_router.py")
        cv_text = _read(REPO_ROOT / "backend" / "routers" / "cv_router.py")
        alias_text = _read(REPO_ROOT / "backend" / "routers" / "normal_search_router.py")

        self.assertIn("INSERT INTO jobs", job_text)
        self.assertIn("FROM jobs", job_text)
        self.assertIn("INSERT INTO cvs", cv_text)
        self.assertIn("FROM cvs", cv_text)
        self.assertIn("search_jobs_response", alias_text)
        self.assertIn("search_cvs_response", alias_text)

        combined = "\n".join([job_text, cv_text, alias_text])
        self.assertNotIn("job_posts_v2", combined)
        self.assertNotIn("candidate_profiles_v2", combined)
        self.assertNotIn("backend/db_v2/scenario", combined)
        self.assertNotIn("backend/db_v2/scenarios", combined)


if __name__ == "__main__":
    unittest.main()
