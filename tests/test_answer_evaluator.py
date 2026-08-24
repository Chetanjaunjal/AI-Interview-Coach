"""Commit #10 tests for rubric validation, scoring, and evaluator behavior."""

import json
import unittest
from types import SimpleNamespace

from ai.answer_evaluator import (
    AnswerEvaluator,
    build_evaluation_prompt,
    parse_json_response,
    validate_and_score_evaluation,
)


TECHNICAL_EVALUATION = {
    "relevance": 8,
    "technical_correctness": 7,
    "completeness": 6,
    "communication": 8,
    "strengths": ["Addresses the question"],
    "weaknesses": ["Needs more detail"],
    "missing_points": ["An example"],
    "improvement_suggestions": ["Add an example"],
    "model_feedback": "A useful answer with room to expand.",
}


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.payload))]
        )


class AnswerEvaluatorTests(unittest.TestCase):
    def test_technical_evaluation_calculates_weighted_score(self):
        result = validate_and_score_evaluation(TECHNICAL_EVALUATION, "Technical")
        self.assertEqual(result["overall_score"], 7.2)

    def test_hr_uses_content_quality(self):
        response = {
            **{key: value for key, value in TECHNICAL_EVALUATION.items() if key != "technical_correctness"},
            "content_quality": 9,
        }
        result = validate_and_score_evaluation(response, "HR")
        self.assertEqual(result["overall_score"], 7.9)
        self.assertIn("content_quality", result)
        self.assertNotIn("technical_correctness", result)

    def test_behavioral_uses_content_quality(self):
        response = {
            **{key: value for key, value in TECHNICAL_EVALUATION.items() if key != "technical_correctness"},
            "content_quality": 8,
        }
        result = validate_and_score_evaluation(response, "Behavioral")
        self.assertIsNotNone(result)

    def test_score_outside_range_is_rejected(self):
        invalid = {**TECHNICAL_EVALUATION, "relevance": 11}
        self.assertIsNone(validate_and_score_evaluation(invalid, "Technical"))

    def test_missing_field_is_rejected(self):
        invalid = {key: value for key, value in TECHNICAL_EVALUATION.items() if key != "strengths"}
        self.assertIsNone(validate_and_score_evaluation(invalid, "Technical"))

    def test_invalid_json_is_graceful(self):
        result = AnswerEvaluator(FakeClient("not json"), "test").evaluate(
            "What is Python?", "A language.", "Technical", "Easy", "Python", {}
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "AI returned invalid evaluation data.")

    def test_api_failure_is_graceful(self):
        class FailingClient:
            chat = SimpleNamespace(completions=SimpleNamespace(create=self.fail))

            @staticmethod
            def fail(**kwargs):
                raise RuntimeError("service unavailable")

        result = AnswerEvaluator(FailingClient(), "test").evaluate(
            "What is Python?", "A language.", "Technical", "Easy", "Python", {}
        )
        self.assertFalse(result["success"])
        self.assertIn("temporarily unavailable", result["error"])

    def test_prompt_uses_only_relevant_context(self):
        prompt = build_evaluation_prompt(
            "What is Flask?", "A Python web framework.", "Technical", "Easy", "Flask",
            {"required_skills": ["Python"], "preferred_skills": ["Docker"], "raw": "omit"},
        )
        self.assertIn("What is Flask?", prompt)
        self.assertIn("Python", prompt)
        self.assertNotIn("raw", prompt)

    def test_code_fenced_json_is_parsed(self):
        self.assertEqual(
            parse_json_response("```json\n" + json.dumps(TECHNICAL_EVALUATION) + "\n```"),
            TECHNICAL_EVALUATION,
        )


if __name__ == "__main__":
    unittest.main()
