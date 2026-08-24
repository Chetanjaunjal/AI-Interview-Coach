"""Commit #9 tests for the Flask-session interview workflow."""

import unittest

from app import app


class InterviewSessionTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()
        with self.client.session_transaction() as flask_session:
            flask_session.clear()
            flask_session["generated_questions"] = self.questions(5)
            flask_session["generated_interview_config"] = {
                "interview_type": "technical",
                "difficulty": "medium",
                "total_questions": 5,
            }

    @staticmethod
    def questions(count):
        return [
            {
                "id": index,
                "question": f"Question {index}",
                "category": "Technical",
                "difficulty": "Medium",
                "topic": "Python",
                "reason": "Based on the role",
            }
            for index in range(1, count + 1)
        ]

    def test_start_interview_shows_question_one_of_five(self):
        response = self.client.post("/start-interview")
        self.assertEqual(response.status_code, 302)
        interview_page = self.client.get(response.location)
        self.assertEqual(interview_page.status_code, 200)
        self.assertIn(b"Question 1", interview_page.data)
        self.assertIn(b"of 5", interview_page.data)

    def test_valid_answer_is_saved_and_question_two_appears(self):
        self.client.post("/start-interview")
        response = self.client.post(
            "/submit-answer",
            data={"question_id": "1", "answer": "My answer"},
        )
        self.assertEqual(response.status_code, 302)
        next_page = self.client.get(response.location)
        self.assertIn(b"Question 2", next_page.data)
        with self.client.session_transaction() as flask_session:
            self.assertEqual(flask_session["interview"]["answers"][0]["question_id"], 1)

    def test_empty_answer_stays_on_same_question(self):
        self.client.post("/start-interview")
        response = self.client.post(
            "/submit-answer", data={"question_id": "1", "answer": "   "}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Please provide an answer before continuing", response.data)
        self.assertIn(b"Question 1", response.data)

    def test_completing_all_questions_shows_summary(self):
        self.client.post("/start-interview")
        for index in range(1, 6):
            response = self.client.post(
                "/submit-answer",
                data={"question_id": str(index), "answer": f"Answer {index}"},
            )
        self.assertEqual(response.status_code, 302)
        summary = self.client.get(response.location)
        self.assertEqual(summary.status_code, 200)
        self.assertIn(b"Interview Completed", summary.data)
        self.assertIn(b"5 out of 5", summary.data)
        self.assertNotIn(b"Match Score", summary.data)

    def test_refresh_keeps_current_question_and_saved_answers(self):
        self.client.post("/start-interview")
        self.client.post(
            "/submit-answer", data={"question_id": "1", "answer": "Saved answer"}
        )
        refreshed = self.client.get("/interview")
        self.assertIn(b"Question 2", refreshed.data)
        with self.client.session_transaction() as flask_session:
            self.assertEqual(len(flask_session["interview"]["answers"]), 1)

    def test_interview_without_start_redirects_home(self):
        with self.client.session_transaction() as flask_session:
            flask_session.clear()
        response = self.client.get("/interview")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")

    def test_duplicate_or_stale_submission_is_not_added(self):
        self.client.post("/start-interview")
        self.client.post(
            "/submit-answer", data={"question_id": "1", "answer": "First answer"}
        )
        duplicate = self.client.post(
            "/submit-answer", data={"question_id": "1", "answer": "First answer"}
        )
        self.assertEqual(duplicate.status_code, 400)
        with self.client.session_transaction() as flask_session:
            self.assertEqual(len(flask_session["interview"]["answers"]), 1)

    def test_new_interview_resets_previous_state(self):
        self.client.post("/start-interview")
        self.client.post(
            "/submit-answer", data={"question_id": "1", "answer": "Old answer"}
        )
        self.client.post("/start-interview")
        with self.client.session_transaction() as flask_session:
            interview_state = flask_session["interview"]
            self.assertEqual(interview_state["current_index"], 0)
            self.assertEqual(interview_state["answers"], [])

    def test_tampered_question_id_is_rejected(self):
        self.client.post("/start-interview")
        response = self.client.post(
            "/submit-answer", data={"question_id": "999", "answer": "Answer"}
        )
        self.assertEqual(response.status_code, 400)
        with self.client.session_transaction() as flask_session:
            self.assertEqual(flask_session["interview"]["answers"], [])

    def test_oversized_answer_is_rejected(self):
        self.client.post("/start-interview")
        response = self.client.post(
            "/submit-answer",
            data={"question_id": "1", "answer": "a" * 10001},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"too long", response.data)


if __name__ == "__main__":
    unittest.main()
