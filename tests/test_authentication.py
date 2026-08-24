import os
import tempfile
import unittest

from app import app
from database.db import create_user, get_user_by_email, get_user_interview, init_database, save_completed_interview


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.original_database_path = app.config.get("DATABASE_PATH")
        self.database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.database.close()
        app.config.update(TESTING=True, SECRET_KEY="auth-test-secret", DATABASE_PATH=self.database.name)
        init_database(app)
        self.client = app.test_client()

    def tearDown(self):
        os.unlink(self.database.name)
        app.config["DATABASE_PATH"] = self.original_database_path

    def register(self, email="a@example.com", password="password123"):
        return self.client.post("/register", data={"name": "User A", "email": email, "password": password, "confirmation": password})

    def test_registration_stores_hash_not_password(self):
        response = self.register()
        self.assertEqual(response.status_code, 302)
        user = get_user_by_email("a@example.com", app)
        self.assertNotEqual(user["password_hash"], "password123")
        self.assertTrue(user["password_hash"])

    def test_duplicate_and_mismatched_registration_are_rejected(self):
        self.register()
        duplicate = self.register()
        mismatch = self.client.post("/register", data={"name": "Other", "email": "b@example.com", "password": "password123", "confirmation": "different"})
        self.assertEqual(duplicate.status_code, 200)
        self.assertIn(b"already exists", duplicate.data)
        self.assertIn(b"do not match", mismatch.data)

    def test_login_logout_and_protected_route(self):
        self.register()
        self.client.post("/login", data={"email": "a@example.com", "password": "password123"})
        self.assertEqual(self.client.get("/history").status_code, 200)
        self.client.post("/logout")
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_wrong_password_is_generic(self):
        self.register()
        response = self.client.post("/login", data={"email": "a@example.com", "password": "wrongpass"})
        self.assertIn(b"Invalid email or password", response.data)

    def test_user_cannot_read_another_users_interview(self):
        user_a = get_user_by_email("a@example.com", app)
        user_b_id = create_user("User B", "b@example.com", "hash", app)
        completed = {"questions": [{"id": 1, "question": "Q", "category": "Technical", "difficulty": "Easy", "topic": "Python"}], "answers": [{"question_id": 1, "answer": "A", "evaluation": {"overall_score": 8}}], "interview_type": "technical", "difficulty": "easy"}
        interview_id = save_completed_interview(completed, {"overall_score": 8}, user_a["id"], app)
        self.assertIsNotNone(get_user_interview(interview_id, user_a["id"], app))
        self.assertIsNone(get_user_interview(interview_id, user_b_id, app))


if __name__ == "__main__":
    unittest.main()
