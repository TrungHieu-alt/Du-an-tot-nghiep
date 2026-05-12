"""Guardrails against external AI or embedding API clients."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

FORBIDDEN_RUNTIME_MODULES = {
    "openai",
    "google.generativeai",
    "google.genai",
    "cohere",
    "anthropic",
}
FORBIDDEN_ENV_KEYS = {
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "COHERE_API_KEY",
    "HUGGINGFACE_API_KEY",
    "HF_TOKEN",
}
FORBIDDEN_REQUIREMENT_NAMES = {
    "openai",
    "google-generativeai",
    "cohere",
    "anthropic",
}


class NoExternalAIClientTests(unittest.TestCase):
    def test_runtime_python_does_not_import_external_ai_clients(self):
        offenders: list[str] = []
        for path in BACKEND_ROOT.rglob("*.py"):
            if "__pycache__" in path.parts or "tests" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                else:
                    continue
                for module in modules:
                    if module in FORBIDDEN_RUNTIME_MODULES:
                        offenders.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

        self.assertEqual(offenders, [])

    def test_requirements_do_not_include_external_ai_api_clients(self):
        requirements = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")
        normalized = {
            line.split("==", 1)[0].strip().lower()
            for line in requirements.splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        self.assertTrue({"sentence-transformers"}.issubset(normalized))
        self.assertEqual(normalized & FORBIDDEN_REQUIREMENT_NAMES, set())

    def test_env_example_has_no_external_ai_api_keys(self):
        env_path = REPO_ROOT / ".env.example"
        if not env_path.exists():
            self.skipTest(".env.example is outside the backend-only Docker test mount")
        env_example = env_path.read_text(encoding="utf-8")
        present = sorted(key for key in FORBIDDEN_ENV_KEYS if key in env_example)
        self.assertEqual(present, [])


if __name__ == "__main__":
    unittest.main()
