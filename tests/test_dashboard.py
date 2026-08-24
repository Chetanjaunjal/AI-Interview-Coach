"""Commit #11 dashboard route tests."""

import unittest

from app import app


class DashboardRouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="dashboard-test-secret")
        self.client = app.test_client()

    def test_no_completed_interview_redirects_with_message(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")

    def test_completed_interview_renders_dashboard(self):
        questions = [
            {"id": 1, "question": "Explain Python", "category": "Technical", "difficulty": "Easy", "topic": "Python"},
            {"id": 2, "question": "Tell me about yourself", "category": "HR", "difficulty": "Easy", "topic": "Motivation"},
        ]
        answers = [
            {"question_id": 1, "question": "Explain Python", "category": "Technical", "topic": "Python", "answer": "A language", "evaluation": {"overall_score": 8, "relevance": 8, "technical_correctness": 8, "completeness": 8, "communication": 8}},
            {"question_id": 2, "question": "Tell me about yourself", "category": "HR", "topic": "Motivation", "answer": "My answer", "evaluation": {"overall_score": 6, "relevance": 6, "content_quality": 6, "completeness": 6, "communication": 6}},
        ]
        with self.client.session_transaction() as flask_session:
            flask_session["completed_interview"] = {
                "questions": questions,
                "current_index": 2,
                "answers": answers,
                "total_questions": 2,
            }
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Interview Performance", response.data)
        self.assertIn(b"7.0", response.data)
        self.assertIn(b"Python", response.data)


if __name__ == "__main__":
    unittest.main()
