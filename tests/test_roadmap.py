import unittest

from analytics.roadmap import build_daily_plan, build_roadmap


class RoadmapTests(unittest.TestCase):
    def area(self, topic, score, practice_average=None, recent_average=None, attempts=4):
        return {"topic": topic, "average_score": score, "practice_average": practice_average, "recent_average": recent_average, "attempts": attempts, "questions": attempts, "practice_attempts": 2, "trend": "improving", "missing_concepts": ["JOIN"]}

    def test_no_data_returns_empty_roadmap(self):
        result = build_roadmap({"weak_topics": [], "strong_topics": [], "has_data": False})
        self.assertFalse(result["has_data"])
        self.assertEqual(result["topics"], [])

    def test_low_topic_has_high_priority_and_needs_improvement(self):
        result = build_roadmap({"weak_topics": [self.area("SQL", 4.2)], "strong_topics": [], "has_data": True})
        sql = result["topics"][0]
        self.assertEqual(sql["status"], "Needs Significant Improvement")
        self.assertGreaterEqual(sql["priority_score"], 50)
        self.assertEqual(sql["recommended_difficulty"], "easy")

    def test_strong_topic_is_classified_strong(self):
        result = build_roadmap({"weak_topics": [], "strong_topics": [self.area("Java", 9)], "has_data": True})
        self.assertEqual(result["topics"][0]["status"], "Strong")
        self.assertEqual(result["topics"][0]["recommended_difficulty"], "hard")

    def test_job_relevance_increases_priority(self):
        area = self.area("SQL", 5)
        general = build_roadmap({"weak_topics": [area], "strong_topics": [], "has_data": True})["topics"][0]
        job = {"title": "Backend Developer", "matching_data": {"matched_required_skills": [], "missing_required_skills": ["SQL"]}}
        relevant = build_roadmap({"weak_topics": [area], "strong_topics": [], "has_data": True}, active_job=job)["topics"][0]
        self.assertGreater(relevant["priority_score"], general["priority_score"])

    def test_daily_plan_matches_requested_duration(self):
        roadmap = {"topics": [{"topic": "SQL"}]}
        for duration in (30, 60, 90):
            plan = build_daily_plan(roadmap, duration)
            self.assertEqual(sum(minutes for minutes, _ in plan["tasks"]), duration)


if __name__ == "__main__":
    unittest.main()
