import unittest
from pathlib import Path

from core.preprocess import analyze_text_quality, preprocess_text, split_text_into_chunks


class TextPreprocessTests(unittest.TestCase):
    def test_null_byte_cleanup(self):
        self.assertEqual(preprocess_text("Nguyen\x00 Van A"), "Nguyen Van A")

    def test_replacement_character_cleanup(self):
        self.assertEqual(preprocess_text("Backend\ufffd Engineer"), "Backend Engineer")

    def test_excessive_whitespace_cleanup(self):
        self.assertEqual(preprocess_text("Python\t\t  FastAPI    PostgreSQL"), "Python FastAPI PostgreSQL")

    def test_excessive_newline_and_bullet_cleanup(self):
        dirty = "Name\r\n\r\n\r\n• Skills\r\n– React\r\n— Node.js"
        self.assertEqual(preprocess_text(dirty), "Name\n\n- Skills\n- React\n- Node.js")

    def test_short_and_bad_text_quality_warnings(self):
        quality = analyze_text_quality("\x00\ufffd!!! 12345")

        self.assertFalse(quality["is_usable"])
        self.assertIn("text_too_short", quality["warnings"])
        self.assertIn("too_many_non_letter_characters", quality["warnings"])
        self.assertIn("too_many_bad_encoding_characters", quality["warnings"])

    def test_empty_text_quality_warning(self):
        quality = analyze_text_quality("\x00\ufffd")

        self.assertFalse(quality["is_usable"])
        self.assertIn("empty_text", quality["warnings"])

    def test_chunk_splitting(self):
        text = " ".join(f"word{i}" for i in range(80))
        chunks = split_text_into_chunks(text, max_chars=80)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 80 for chunk in chunks))
        self.assertEqual(" ".join(chunks).replace("\n", " "), preprocess_text(text))

    def test_local_model_module_is_not_required(self):
        backend_root = Path(__file__).resolve().parents[1]
        removed_module = "trans" + "lator.py"
        forbidden_terms = [
            "core." + "trans" + "lator",
            "trans" + "late_text",
            "facebook/" + "n" + "llb",
            "trans" + "formers",
        ]

        self.assertFalse((backend_root / "core" / removed_module).exists())
        for relative_path in [
            "core/preprocess.py",
            "routers/cv_router.py",
            "routers/job_router.py",
        ]:
            source = (backend_root / relative_path).read_text(encoding="utf-8")
            for forbidden_term in forbidden_terms:
                self.assertNotIn(forbidden_term, source)


if __name__ == "__main__":
    unittest.main()
