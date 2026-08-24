import os
import tempfile
import unittest
from types import SimpleNamespace

from analytics.job_preparation import build_job_interview_plan
from database.db import create_job, create_user, get_user_job, get_user_interviews, init_database, save_completed_interview, update_job_matching


class JobPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = SimpleNamespace(config={"DATABASE_PATH": os.path.join(self.temp_dir.name, "coach.db")})
        init_database(self.app)
        self.user_id = create_user("User", "job@example.com", "hash", self.app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_job_is_user_scoped_and_matching_data_persists(self):
        job_id = create_job(self.user_id, "Backend Developer", "Example", "Long description", {"job_title": "Backend Developer", "required_skills": ["Java", "SQL"], "preferred_skills": ["Docker"]}, self.app)
        update_job_matching(job_id, self.user_id, {"matched_required_skills": [{"job_skill": "Java"}], "missing_required_skills": ["SQL"], "missing_preferred_skills": ["Docker"]}, self.app)
        job = get_user_job(job_id, self.user_id, self.app)
        self.assertEqual(job["matching_data"]["missing_required_skills"], ["SQL"])
        self.assertIsNone(get_user_job(job_id, self.user_id + 1, self.app))

    def test_plan_contains_gaps_and_weak_areas(self):
        plan = build_job_interview_plan({"job_title": "Backend Developer", "required_skills": ["SQL"]}, {"matched_required_skills": [], "missing_required_skills": ["SQL"], "missing_preferred_skills": []}, {"has_data": True, "weak_topics": [{"topic": "SQL"}]}, "medium", 10)
        self.assertEqual(plan["role"], "Backend Developer")
        self.assertIn("SQL", plan["missing_skills"])
        self.assertIn("SQL", plan["weak_areas"])
        self.assertEqual(sum(plan["question_distribution"].values()), 10)

    def test_interview_remembers_job_id(self):
        job_id = create_job(self.user_id, "Data Analyst", None, "Long description", {"job_title": "Data Analyst"}, self.app)
        completed = {"questions": [{"id": 1, "question": "Q", "category": "Technical", "difficulty": "Easy", "topic": "SQL"}], "answers": [{"question_id": 1, "answer": "A", "evaluation": {"overall_score": 7}}], "interview_type": "job-specific", "difficulty": "easy"}
        interview_id = save_completed_interview(completed, {"overall_score": 7}, self.user_id, self.app, job_id)
        self.assertEqual(get_user_interviews(self.user_id, self.app)[0]["job_title"], "Data Analyst")


if __name__ == "__main__":
    unittest.main()
