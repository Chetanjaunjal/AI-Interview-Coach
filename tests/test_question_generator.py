"""Commit #8 tests for validation, prompt context, and AI response handling."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ai.question_generator import (
    QuestionGenerator,
    build_prompt,
    generate_interview_questions,
    parse_json_response,
    validate_question_response,
)


RESUME = {
    "skills": ["Python", "Flask"],
    "projects": ["AI Interview Coach"],
    "experience": ["Software Intern"],
    "certifications": ["AWS Cloud Practitioner"],
    "education": ["B.S. Computer Science"],
}
JOB = {
    "job_title": "Python Engineer",
    "required_skills": ["Python", "REST APIs"],
    "preferred_skills": ["Docker"],
    "responsibilities": ["Build web services"],
    "qualifications": ["Strong problem solving"],
}
MATCH = {
    "matched_required_skills": [{"job_skill": "Python", "match_type": "exact"}],
    "missing_required_skills": ["REST APIs"],
    "missing_preferred_skills": ["Docker"],
    "semantic_matches": [],
}


def question_payload(count=5, difficulty="easy"):
    return {
        "questions": [
            {
                "question": f"Explain Python concept {index}.",
                "category": "Technical",
                "difficulty": difficulty,
                "topic": "Python",
                "reason": "Based on the candidate skills and target role.",
            }
            for index in range(count)
        ]
    }


class FakeClient:
    def __init__(self, content):
        self.content = content
        self.request = None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class QuestionGeneratorTests(unittest.TestCase):
    def test_technical_easy_five_questions(self):
        result = QuestionGenerator(FakeClient(json.dumps(question_payload())), "test").generate(
            RESUME, JOB, MATCH, "technical", "easy", 5
        )
        self.assertTrue(result["success"])
        self.assertEqual(len(result["questions"]), 5)

    def test_technical_hard_ten_questions(self):
        result = QuestionGenerator(
            FakeClient(json.dumps(question_payload(10, "hard"))), "test"
        ).generate(RESUME, JOB, MATCH, "technical", "hard", 10)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["questions"]), 10)

    def test_hr_medium_five_questions(self):
        result = QuestionGenerator(
            FakeClient(json.dumps(question_payload(5, "medium"))), "test"
        ).generate(RESUME, JOB, MATCH, "hr", "medium", 5)
        self.assertTrue(result["success"])

    def test_behavioral_medium_five_questions(self):
        result = QuestionGenerator(
            FakeClient(json.dumps(question_payload(5, "medium"))), "test"
        ).generate(RESUME, JOB, MATCH, "behavioral", "medium", 5)
        self.assertTrue(result["success"])

    def test_mixed_hard_fifteen_questions(self):
        result = QuestionGenerator(
            FakeClient(json.dumps(question_payload(15, "hard"))), "test"
        ).generate(RESUME, JOB, MATCH, "mixed", "hard", 15)
        self.assertTrue(result["success"])

    def test_invalid_interview_type(self):
        result = generate_interview_questions(RESUME, JOB, MATCH, "panel", "easy", 5)
        self.assertFalse(result["success"])

    def test_invalid_difficulty(self):
        result = generate_interview_questions(RESUME, JOB, MATCH, "technical", "expert", 5)
        self.assertFalse(result["success"])

    def test_invalid_question_count(self):
        result = generate_interview_questions(RESUME, JOB, MATCH, "technical", "easy", 100)
        self.assertFalse(result["success"])

    def test_missing_resume_analysis(self):
        result = generate_interview_questions({}, JOB, MATCH, "technical", "easy", 5)
        self.assertFalse(result["success"])

    def test_missing_job_analysis(self):
        result = generate_interview_questions(RESUME, {}, MATCH, "technical", "easy", 5)
        self.assertFalse(result["success"])

    def test_malformed_json(self):
        client = FakeClient("not json")
        result = QuestionGenerator(client, "test").generate(
            RESUME, JOB, MATCH, "technical", "easy", 5
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AI returned invalid question data.")

    def test_prompt_uses_structured_context_and_not_raw_resume(self):
        prompt = build_prompt(RESUME, JOB, MATCH, "technical", "medium", 5)
        self.assertIn("AI Interview Coach", prompt)
        self.assertIn("REST APIs", prompt)
        self.assertNotIn("raw resume text", prompt)

    def test_focused_prompt_includes_topic_and_missed_concepts(self):
        prompt = build_prompt(RESUME, JOB, MATCH, "technical", "medium", 5, "SQL", ["JOIN", "GROUP BY"])
        self.assertIn("SQL", prompt)
        self.assertIn("GROUP BY", prompt)
        self.assertIn("Do not ask unrelated questions", prompt)

    def test_duplicate_questions_are_rejected(self):
        payload = question_payload()
        payload["questions"][1]["question"] = payload["questions"][0]["question"]
        self.assertIsNone(validate_question_response(payload, "easy", 5))

    def test_json_with_code_fence_is_parsed(self):
        content = "```json\n" + json.dumps(question_payload()) + "\n```"
        self.assertEqual(parse_json_response(content), question_payload())


if __name__ == "__main__":
    unittest.main()
