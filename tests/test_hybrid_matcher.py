"""
Integration tests for Hybrid Matching (Commit #7)

Tests the combination of exact matching and semantic matching
in the full matching pipeline.

Run with: python -m pytest tests/test_hybrid_matcher.py -v
"""

import unittest
from ai.matcher import (
    find_hybrid_matches,
    match_resume_to_job,
    normalize_skill,
    SEMANTIC_SIMILARITY_THRESHOLD,
)


class TestHybridMatching(unittest.TestCase):
    """Test the hybrid exact + semantic matching function."""

    def test_exact_match_recognized(self):
        """Exact matches should be identified as 'exact' type."""
        candidate = ["Java", "Python"]
        job = ["Java", "SQL"]
        
        matched, missing, semantic = find_hybrid_matches(candidate, job)
        
        # Should have at least one exact match
        exact_matches = [m for m in matched if m.get("match_type") == "exact"]
        self.assertGreater(len(exact_matches), 0)
        
        # Java should be in exact matches
        java_match = [m for m in exact_matches if m.get("candidate_skill") == "Java"]
        self.assertGreater(len(java_match), 0)

    def test_case_insensitive_exact_matching(self):
        """Exact matching should be case-insensitive (via normalization)."""
        candidate = ["java"]
        job = ["JAVA"]
        
        matched, missing, semantic = find_hybrid_matches(candidate, job)
        
        # Should match despite different cases
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["match_type"], "exact")

    def test_semantic_match_recognized(self):
        """Semantic matches should be identified as 'semantic' type."""
        candidate = ["REST API development"]
        job = ["RESTful API"]
        
        matched, missing, semantic = find_hybrid_matches(
            candidate, 
            job,
            threshold=0.70
        )
        
        # Should have semantic match
        self.assertGreater(len(semantic), 0)
        self.assertEqual(semantic[0]["match_type"], "semantic")

    def test_missing_skills_identified(self):
        """Skills with no match should be in missing list."""
        candidate = ["Java", "Python"]
        job = ["Java", "Spring Boot", "AWS"]
        
        matched, missing, semantic = find_hybrid_matches(
            candidate,
            job,
            threshold=0.75
        )
        
        # Spring Boot and AWS should be missing
        self.assertIn("Spring Boot", missing)
        self.assertIn("AWS", missing)

    def test_java_javascript_not_matched(self):
        """Java and JavaScript should NOT be matched."""
        candidate = ["JavaScript"]
        job = ["Java"]
        
        matched, missing, semantic = find_hybrid_matches(
            candidate,
            job,
            threshold=0.75
        )
        
        # Should have no match
        self.assertEqual(len(matched), 0)
        self.assertIn("Java", missing)

    def test_python_pytorch_not_matched(self):
        """Python and PyTorch should NOT be matched."""
        candidate = ["PyTorch"]
        job = ["Python"]
        
        matched, missing, semantic = find_hybrid_matches(
            candidate,
            job,
            threshold=0.75
        )
        
        # Should have no match at threshold 0.75
        self.assertEqual(len(matched), 0)

    def test_empty_candidate_skills(self):
        """Empty candidate list should return no matches."""
        candidate = []
        job = ["Java", "SQL"]
        
        matched, missing, semantic = find_hybrid_matches(candidate, job)
        
        self.assertEqual(len(matched), 0)
        self.assertEqual(len(missing), 2)

    def test_empty_job_skills(self):
        """Empty job skills list should return empty missing."""
        candidate = ["Java", "Python"]
        job = []
        
        matched, missing, semantic = find_hybrid_matches(candidate, job)
        
        self.assertEqual(len(missing), 0)

    def test_threshold_affects_semantic_matching(self):
        """Lowering threshold should increase semantic matches."""
        candidate = ["REST API development"]
        job = ["RESTful API", "GraphQL"]
        
        # High threshold
        matched_high, missing_high, semantic_high = find_hybrid_matches(
            candidate,
            job,
            threshold=0.90
        )
        
        # Lower threshold
        matched_low, missing_low, semantic_low = find_hybrid_matches(
            candidate,
            job,
            threshold=0.60
        )
        
        # Lower threshold should match more
        self.assertGreaterEqual(len(matched_low), len(matched_high))

    def test_similarity_scores_included(self):
        """Semantic matches should include similarity scores."""
        candidate = ["REST API development"]
        job = ["RESTful API"]
        
        matched, missing, semantic = find_hybrid_matches(
            candidate,
            job,
            threshold=0.70
        )
        
        if semantic:
            # Should have similarity score
            self.assertIn("similarity", semantic[0])
            similarity = semantic[0]["similarity"]
            # Should be a float between 0 and 1
            self.assertIsInstance(similarity, float)
            self.assertGreaterEqual(similarity, 0.70)


class TestFullMatchingPipeline(unittest.TestCase):
    """Test the complete matching pipeline with hybrid matching."""

    def test_match_with_semantic_skills(self):
        """Full matching pipeline should use semantic matching."""
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java", "REST API development", "SQL"]
            }
        }
        
        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java", "RESTful API"],
                "preferred_skills": ["MySQL", "Docker"]
            }
        }
        
        result = match_resume_to_job(resume_analysis, job_analysis)
        
        self.assertTrue(result["success"])
        match_result = result["result"]
        
        # Should have matched skills
        self.assertGreater(match_result["match_percentage"], 0)
        
        # Should have semantic matches in result
        self.assertIn("semantic_matches", match_result)

    def test_match_distinguishes_exact_and_semantic(self):
        """Result should clearly show exact vs semantic matches."""
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java", "REST API development"]
            }
        }
        
        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java", "RESTful API"],
                "preferred_skills": []
            }
        }
        
        result = match_resume_to_job(resume_analysis, job_analysis)
        
        match_result = result["result"]
        
        # Should have exact_matches list
        self.assertIn("exact_matches", match_result)
        # Should have semantic_matches list
        self.assertIn("semantic_matches", match_result)

    def test_comprehensive_skill_matching(self):
        """Test a comprehensive scenario with multiple skill types."""
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": [
                    "Java",           # Exact match with job required
                    "REST API dev",   # Semantic match with job required "RESTful API"
                    "OOP",            # Bonus skill
                    "Unit Testing",   # Bonus skill
                    "SQL"             # Exact match with job preferred
                ]
            }
        }
        
        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java", "RESTful API"],
                "preferred_skills": ["SQL", "AWS"]
            }
        }
        
        result = match_resume_to_job(resume_analysis, job_analysis)
        
        self.assertTrue(result["success"])
        match_result = result["result"]
        
        # Should be a good match (at least 50%)
        self.assertGreater(match_result["match_percentage"], 50)
        
        # Should have matched required skills
        self.assertGreater(len(match_result["matched_required_skills"]), 0)
        
        # Should have additional skills
        self.assertGreater(len(match_result["additional_candidate_skills"]), 0)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in hybrid matching."""

    def test_invalid_resume_analysis(self):
        """Invalid resume analysis should return error."""
        resume_analysis = None
        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java"],
                "preferred_skills": []
            }
        }
        
        result = match_resume_to_job(resume_analysis, job_analysis)
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_unsuccessful_resume_analysis(self):
        """Resume analysis marked unsuccessful should return error."""
        resume_analysis = {
            "success": False,
            "error": "Resume could not be analyzed"
        }
        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java"],
                "preferred_skills": []
            }
        }
        
        result = match_resume_to_job(resume_analysis, job_analysis)
        
        self.assertFalse(result["success"])

    def test_no_skills_in_resume(self):
        """No skills in resume should return error."""
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": []
            }
        }
        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java"],
                "preferred_skills": []
            }
        }
        
        result = match_resume_to_job(resume_analysis, job_analysis)
        
        self.assertFalse(result["success"])

    def test_no_skills_in_job(self):
        """No skills in job should return error."""
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java"]
            }
        }
        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": [],
                "preferred_skills": []
            }
        }
        
        result = match_resume_to_job(resume_analysis, job_analysis)
        
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
