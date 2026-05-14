import unittest

from core.normalizers import (
    normalize_education_level,
    normalize_employment_type,
    normalize_employment_types,
    normalize_language_level,
    normalize_pre_screen_question_type,
    normalize_remote_type,
    normalize_seniority,
    normalize_skill_level,
    normalize_skill_name,
)


class NormalizerTests(unittest.TestCase):
    def test_skill_level_mapping(self):
        cases = [
            ("Good knowledge of React", "intermediate"),
            ("Strong experience with Python", "advanced"),
            ("Basic SQL", "beginner"),
            ("Thành thạo Excel", "advanced"),
            ("Chuyên sâu về kế toán thuế", "expert"),
            (None, "unknown"),
            ("", "unknown"),
            ("random value", "unknown"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_skill_level(value), expected)

    def test_seniority_mapping(self):
        cases = [
            ("intern", "intern"),
            ("thực tập sinh", "intern"),
            ("fresh graduate", "fresher"),
            ("mới ra trường", "fresher"),
            ("1 year experience", "junior"),
            ("2-4 years experience", "middle"),
            ("3 năm kinh nghiệm", "middle"),
            ("5+ years experience", "senior"),
            ("tech lead", "lead"),
            ("engineering manager", "manager"),
            ("head of engineering", "director"),
            (None, "unknown"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_seniority(value), expected)

    def test_employment_type_mapping(self):
        cases = [
            ("full-time", "fulltime"),
            ("permanent", "fulltime"),
            ("toàn thời gian", "fulltime"),
            ("part-time", "parttime"),
            ("bán thời gian", "parttime"),
            ("fixed-term contract", "contract"),
            ("hợp đồng", "contract"),
            ("internship", "internship"),
            ("freelance", "freelance"),
            ("temporary", "temporary"),
            (None, "unknown"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_employment_type(value), expected)
        self.assertEqual(normalize_employment_types(["full-time", "fulltime", "bad"]), ["fulltime"])
        self.assertEqual(normalize_employment_types([]), ["unknown"])

    def test_remote_type_mapping(self):
        cases = [
            ("on-site", "onsite"),
            ("work at office", "onsite"),
            ("làm tại văn phòng", "onsite"),
            ("work from home", "remote"),
            ("wfh", "remote"),
            ("làm từ xa", "remote"),
            ("hybrid", "hybrid"),
            ("2 days office, 3 days remote", "hybrid"),
            ("kết hợp văn phòng và từ xa", "hybrid"),
            (None, "unknown"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_remote_type(value), expected)

    def test_education_level_mapping(self):
        cases = [
            ("high school", "high_school"),
            ("THPT", "high_school"),
            ("trung cấp", "vocational"),
            ("cao đẳng", "associate"),
            ("university", "bachelor"),
            ("đại học", "bachelor"),
            ("cử nhân", "bachelor"),
            ("engineer degree", "bachelor"),
            ("thạc sĩ", "master"),
            ("MBA", "master"),
            ("tiến sĩ", "phd"),
            ("certificate", "certificate"),
            ("chứng chỉ", "certificate"),
            (None, "unknown"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_education_level(value), expected)

    def test_language_level_mapping(self):
        cases = [
            ("A1", "basic"),
            ("A2", "basic"),
            ("can communicate", "conversational"),
            ("giao tiếp được", "conversational"),
            ("B1", "intermediate"),
            ("B2", "intermediate"),
            ("trung cấp", "intermediate"),
            ("C1", "proficient"),
            ("professional working proficiency", "proficient"),
            ("C2", "fluent"),
            ("fluent", "fluent"),
            ("native", "native"),
            ("bản ngữ", "native"),
            (None, "unknown"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_language_level(value), expected)

    def test_pre_screen_question_type_mapping(self):
        cases = [
            ("short answer", "text"),
            ("paragraph", "text"),
            ("number", "number"),
            ("single choice", "single-choice"),
            ("radio", "single-choice"),
            ("multiple choice", "multi-choice"),
            ("checkbox", "multi-choice"),
            (None, "unknown"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_pre_screen_question_type(value), expected)

    def test_skill_alias_mapping(self):
        cases = [
            ("ReactJS", "react"),
            ("React.js", "react"),
            ("Node.js", "nodejs"),
            ("Postgres", "postgresql"),
            ("MS Excel", "excel"),
            ("Kê khai thuế", "tax_declaration"),
            ("Báo cáo tài chính", "financial_reporting"),
            ("PTS", "photoshop"),
            ("Auto CAD", "autocad"),
            ("Facebook Ads", "meta_ads"),
            ("CSKH", "customer_service"),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(normalize_skill_name(value)["normalized_name"], expected)


if __name__ == "__main__":
    unittest.main()
