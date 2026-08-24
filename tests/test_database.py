import os
import tempfile
import unittest
from types import SimpleNamespace

from database.db import DatabaseError, create_user, delete_interview, get_db_connection, get_interview, init_database, save_completed_interview


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = SimpleNamespace(config={"DATABASE_PATH": os.path.join(self.temp_dir.name, "interviews.db")})
        init_database(self.app)

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def completed(question_count=2):
        questions = [{"id": index, "question": f"Question {index}", "category": "Technical", "difficulty": "Medium", "topic": "Python"} for index in range(1, question_count + 1)]
        answers = [{"question_id": index, "answer": f"Answer {index}", "evaluation": {"relevance": 8, "technical_correctness": 8, "completeness": 7, "communication": 8, "overall_score": 7.8, "model_feedback": "Good answer."}} for index in range(1, question_count + 1)]
        return {"questions": questions, "answers": answers, "interview_type": "technical", "difficulty": "medium"}

    def test_completed_interview_and_children_are_persisted(self):
        interview_id = save_completed_interview(self.completed(), {"overall_score": 7.8}, self.app)
        saved = get_interview(interview_id, self.app)
        self.assertEqual(saved["total_questions"], 2)
        self.assertEqual(len(saved["questions"]), 2)
        self.assertEqual(saved["questions"][0]["answer_text"], "Answer 1")

    def test_failed_save_rolls_back_parent_and_children(self):
        completed = self.completed()
        completed["answers"] = completed["answers"][:1]
        with self.assertRaises(ValueError):
            save_completed_interview(completed, {"overall_score": 7.8}, self.app)
        with get_db_connection(self.app) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM interviews").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0], 0)

    def test_invalid_score_is_rejected(self):
        with self.assertRaises(ValueError):
            save_completed_interview(self.completed(), {"overall_score": 15}, self.app)

    def test_delete_cascades_to_questions_and_answers(self):
        interview_id = save_completed_interview(self.completed(), {"overall_score": 7.8}, self.app)
        self.assertTrue(delete_interview(interview_id, self.app))
        with get_db_connection(self.app) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM interviews").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM answers").fetchone()[0], 0)

    def test_database_error_is_safe_to_handle(self):
        broken_app = SimpleNamespace(config={"DATABASE_PATH": self.temp_dir.name})
        with self.assertRaises(DatabaseError):
            save_completed_interview(self.completed(), {"overall_score": 7.8}, broken_app)

    def test_interview_is_saved_for_the_requested_user(self):
        user_id = create_user("User", "user@example.com", "hash", self.app)
        interview_id = save_completed_interview(self.completed(), {"overall_score": 7.8}, user_id, self.app)
        with get_db_connection(self.app) as connection:
            self.assertEqual(connection.execute("SELECT user_id FROM interviews WHERE id = ?", (interview_id,)).fetchone()[0], user_id)


if __name__ == "__main__":
    unittest.main()
