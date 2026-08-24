"""Commit #11 tests for deterministic interview performance analytics."""

import unittest

from analytics.interview_analytics import calculate_interview_performance


def answer(category="Technical", topic="Python", score=8, correctness=8):
    evaluation = {
        "overall_score": score,
        "relevance": score,
        "completeness": score,
        "communication": score,
    }
    if category == "Technical":
        evaluation["technical_correctness"] = correctness
    else:
        evaluation["content_quality"] = correctness
    return {"category": category, "topic": topic, "answer": "answer", "evaluation": evaluation}


class InterviewAnalyticsTests(unittest.TestCase):
    def test_perfect_interview(self):
        result = calculate_interview_performance([answer(score=10) for _ in range(4)], 4)
        self.assertEqual(result["overall_score"], 10.0)
        self.assertEqual(result["highest_score"], 10.0)
        self.assertEqual(result["lowest_score"], 10.0)

    def test_mixed_performance_average(self):
        result = calculate_interview_performance(
            [answer(score=value, topic=f"Topic {value}") for value in [9, 8, 6, 5]], 4
        )
        self.assertEqual(result["overall_score"], 7.0)
        self.assertEqual(result["answered_questions"], 4)

    def test_only_technical_category(self):
        result = calculate_interview_performance([answer() for _ in range(2)], 2)
        self.assertEqual(result["category_scores"], {"Technical": 8.0})

    def test_all_categories_are_separated(self):
        result = calculate_interview_performance([
            answer("Technical", "Python", 8),
            answer("HR", "Motivation", 7, 7),
            answer("Behavioral", "Conflict", 6, 6),
        ], 3)
        self.assertEqual(result["category_scores"], {"Technical": 8.0, "HR": 7.0, "Behavioral": 6.0})

    def test_hr_without_correctness_field_works(self):
        result = calculate_interview_performance([answer("HR", "Motivation", 8, 9)], 1)
        self.assertEqual(result["averages"]["correctness"], 9.0)

    def test_missing_evaluation_is_ignored_from_scores(self):
        result = calculate_interview_performance([
            answer(score=8),
            {"category": "Technical", "topic": "Python", "answer": "saved", "evaluation_error": "Unavailable"},
        ], 2)
        self.assertEqual(result["answered_questions"], 2)
        self.assertEqual(result["evaluated_questions"], 1)
        self.assertEqual(result["overall_score"], 8.0)

    def test_invalid_score_is_ignored(self):
        invalid = answer(score=15)
        result = calculate_interview_performance([invalid, answer(score=6)], 2)
        self.assertEqual(result["evaluated_questions"], 1)
        self.assertEqual(result["overall_score"], 6.0)

    def test_single_topic_is_not_classified(self):
        result = calculate_interview_performance([answer(topic="SQL", score=5)], 1)
        self.assertEqual(result["topic_scores"], {"SQL": 5.0})
        self.assertNotIn("SQL", result["weak_areas"])
        self.assertEqual(result["topic_question_counts"], {"SQL": 1})

    def test_low_performance_generates_areas_and_recommendations(self):
        result = calculate_interview_performance([
            answer(topic="SQL", score=4, correctness=4),
            answer(topic="SQL", score=5, correctness=5),
        ], 2)
        self.assertIn("SQL", result["weak_areas"])
        self.assertTrue(result["recommendations"])
        self.assertLess(result["averages"]["communication"], 6)


if __name__ == "__main__":
    unittest.main()
