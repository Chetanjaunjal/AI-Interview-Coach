import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from ai.resume_tailor import analyze_resume_keywords, calculate_ats_score, tailor_resume, validate_tailored_output
from database.db import create_job, create_resume, create_tailored_resume, create_user, get_user_tailored_resume, init_database
from utils.pdf_export import resume_to_pdf


class ResumeTailorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = SimpleNamespace(config={"DATABASE_PATH": os.path.join(self.temp_dir.name, "coach.db")})
        init_database(self.app)
        self.user_id = create_user("User", "tailor@example.com", "hash", self.app)
        self.resume = {"name": "User", "skills": ["Java", "Python", "SQL", "Flask"], "projects": ["AI Interview Coach"], "experience": [], "education": ["B.S. Computer Science"], "certifications": [], "summary": "Student"}
        self.job = {"job_title": "Backend Developer", "required_skills": ["Java", "SQL", "Spring Boot"], "preferred_skills": ["Docker"], "responsibilities": ["Build APIs"]}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_skill_is_not_present_and_score_is_deterministic(self):
        keywords = analyze_resume_keywords(self.resume, self.job)
        self.assertIn("Spring Boot", keywords["missing_keywords"])
        self.assertIn("Docker", keywords["missing_keywords"])
        self.assertEqual(calculate_ats_score(keywords, self.resume, self.job), calculate_ats_score(keywords, self.resume, self.job))

    def test_output_rejects_unsupported_skill(self):
        output = {"summary": "", "skills": ["Docker"], "experience": [], "projects": [], "certifications": [], "changes": []}
        self.assertIsNone(validate_tailored_output(output, self.resume))

    def test_tailored_resume_is_scoped_and_pdf_is_valid(self):
        resume_id = create_resume(self.user_id, "resume.pdf", "resume text", self.resume, self.app)
        job_id = create_job(self.user_id, "Backend Developer", None, "Job description", self.job, self.app)
        tailored_id = create_tailored_resume(self.user_id, resume_id, job_id, json.dumps({"summary": "User", "skills": ["Java"], "experience": [], "projects": [], "certifications": [], "changes": []}), 82, self.app)
        self.assertIsNotNone(get_user_tailored_resume(tailored_id, self.user_id, self.app))
        self.assertIsNone(get_user_tailored_resume(tailored_id, self.user_id + 1, self.app))
        pdf = resume_to_pdf({"summary": "User", "skills": ["Java"]})
        self.assertTrue(pdf.startswith(b"%PDF-1.4"))
        self.assertIn(b"%%EOF", pdf)

    def test_ai_failure_is_friendly(self):
        result = tailor_resume(self.resume, self.job, {}, None, None)
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
