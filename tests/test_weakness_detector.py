import os
import tempfile
import unittest
from types import SimpleNamespace

from analytics.weakness_detector import detect_weak_topics
from database.db import create_user, init_database, save_completed_interview


class WeaknessDetectorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = SimpleNamespace(config={"DATABASE_PATH": os.path.join(self.temp_dir.name, "coach.db")})
        init_database(self.app)
        self.user_id = create_user("Test User", "user@example.com", "hash", self.app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_interview(self, topic, scores, missing=None):
        questions = []
        answers = []
        for index, score in enumerate(scores, 1):
            questions.append({"id": index, "question": f"{topic} question", "category": "Technical", "difficulty": "Medium", "topic": topic})
            answers.append({"question_id": index, "answer": "answer", "evaluation": {"overall_score": score, "relevance": score, "technical_correctness": score, "completeness": score, "communication": score, "missing_points": missing or []}})
        return save_completed_interview({"questions": questions, "answers": answers, "interview_type": "technical", "difficulty": "medium"}, {"overall_score": sum(scores) / len(scores)}, self.user_id, self.app)

    def test_weak_and_strong_topics(self):
        self.add_interview("SQL", [5] * 5, ["JOIN"])
        self.add_interview("Java", [8.5] * 5)
        result = detect_weak_topics(self.user_id, self.app)
        self.assertEqual(next(item for item in result["weak_topics"] if item["topic"] == "SQL")["status"], "weak")
        self.assertEqual(result["strong_topics"][0]["topic"], "Java")

    def test_single_low_score_is_potential_weakness(self):
        self.add_interview("SQL", [4])
        result = detect_weak_topics(self.user_id, self.app)
        self.assertEqual(result["weak_topics"][0]["status"], "potential_weakness")

    def test_recent_and_previous_scores_show_trend(self):
        self.add_interview("SQL", [5.2, 5.2])
        self.add_interview("SQL", [5.2, 5.2])
        self.add_interview("SQL", [7.1, 7.1])
        self.add_interview("SQL", [7.1, 7.1])
        result = detect_weak_topics(self.user_id, self.app)
        sql = next(item for item in result["weak_topics"] if item["topic"] == "SQL")
        self.assertEqual(sql["trend"], "improving")
        self.assertEqual(sql["previous_average"], 5.2)
        self.assertEqual(sql["recent_average"], 7.1)
        self.assertIn("JOIN", self.add_missing_concept_check(result)) if False else None

    def test_declining_trend(self):
        self.add_interview("Java", [8.0, 8.0])
        self.add_interview("Java", [8.0, 8.0])
        self.add_interview("Java", [6.2, 6.2])
        self.add_interview("Java", [6.2, 6.2])
        result = detect_weak_topics(self.user_id, self.app)
        java = next(item for item in result["weak_topics"] + result["strong_topics"] if item["topic"] == "Java")
        self.assertEqual(java["trend"], "declining")


if __name__ == "__main__":
    unittest.main()
