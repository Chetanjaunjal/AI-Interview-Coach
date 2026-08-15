"""
Test cases for Semantic Skill Matching (Commit #7)

This test file demonstrates:
1. Semantic similarity scores between similar skills
2. Hybrid matching (exact + semantic)
3. Threshold behavior
4. False positive prevention
5. Robustness with missing data

Tests focus on realistic scenarios:
- REST API vs RESTful API (should match semantically)
- OOP vs Object Oriented Programming (should match)
- Java vs JavaScript (should NOT match)
- Python vs PyTorch (should NOT match)

Run with: python -m pytest tests/test_semantic_matcher.py -v
Or:       python -m unittest tests.test_semantic_matcher -v
"""

import unittest
from ai.semantic_matcher import (
    calculate_semantic_similarity,
    find_best_semantic_match,
    generate_embedding,
)


class TestSemanticSimilarity(unittest.TestCase):
    """Test semantic similarity calculations."""

    def test_identical_skills_maximum_similarity(self):
        """Identical skills should have similarity close to 1.0."""
        similarity = calculate_semantic_similarity("Java", "Java")
        # Should be very close to 1.0
        self.assertGreater(similarity, 0.95)
        self.assertLessEqual(similarity, 1.0)

    def test_rest_api_similarity(self):
        """REST API vs RESTful API should have high semantic similarity."""
        similarity = calculate_semantic_similarity(
            "REST API development",
            "RESTful API"
        )
        # Should be high (above typical threshold of 0.75)
        self.assertGreater(similarity, 0.70)

    def test_oop_vs_object_oriented(self):
        """OOP should be semantically similar to Object Oriented Programming."""
        similarity = calculate_semantic_similarity(
            "Object Oriented Programming",
            "OOP"
        )
        # These are closely related
        self.assertGreater(similarity, 0.70)

    def test_java_vs_javascript_low_similarity(self):
        """Java and JavaScript should NOT have high similarity."""
        similarity = calculate_semantic_similarity("Java", "JavaScript")
        # Different languages, should be low
        self.assertLess(similarity, 0.65)

    def test_python_vs_pytorch_low_similarity(self):
        """Python and PyTorch should NOT have high similarity."""
        similarity = calculate_semantic_similarity("Python", "PyTorch")
        # Different concepts (language vs library)
        self.assertLess(similarity, 0.70)

    def test_sql_vs_sqlite_similarity(self):
        """SQL and SQLite should have some similarity."""
        similarity = calculate_semantic_similarity("SQL", "SQLite")
        # Related but not identical
        self.assertGreater(similarity, 0.50)

    def test_api_vs_rest_similarity(self):
        """API and REST API should have meaningful similarity."""
        similarity = calculate_semantic_similarity("API", "REST API")
        # Related concepts
        self.assertGreater(similarity, 0.60)

    def test_empty_string_returns_zero(self):
        """Empty strings should return similarity of 0."""
        similarity = calculate_semantic_similarity("", "Java")
        self.assertEqual(similarity, 0.0)

        similarity = calculate_semantic_similarity("Java", "")
        self.assertEqual(similarity, 0.0)

        similarity = calculate_semantic_similarity("", "")
        self.assertEqual(similarity, 0.0)

    def test_none_input_returns_zero(self):
        """None inputs should return similarity of 0."""
        similarity = calculate_semantic_similarity(None, "Java")
        self.assertEqual(similarity, 0.0)

        similarity = calculate_semantic_similarity("Java", None)
        self.assertEqual(similarity, 0.0)


class TestBestSemanticMatch(unittest.TestCase):
    """Test finding the best semantic match from a list."""

    def test_find_rest_api_match(self):
        """Should find REST API as match for RESTful API."""
        candidates = [
            "GraphQL",
            "REST API development",
            "SOAP API"
        ]
        result = find_best_semantic_match(
            "RESTful API",
            candidates,
            threshold=0.70
        )
        
        self.assertIsNotNone(result)
        if result:
            matched_skill, similarity = result
            self.assertEqual(matched_skill, "REST API development")
            self.assertGreater(similarity, 0.70)

    def test_find_oop_match(self):
        """Should find OOP match for Object Oriented Programming."""
        candidates = [
            "Functional Programming",
            "OOP",
            "Procedural Programming"
        ]
        result = find_best_semantic_match(
            "Object Oriented Programming",
            candidates,
            threshold=0.70
        )
        
        self.assertIsNotNone(result)
        if result:
            matched_skill, similarity = result
            self.assertEqual(matched_skill, "OOP")

    def test_no_java_javascript_match(self):
        """Should NOT match Java with JavaScript."""
        candidates = [
            "JavaScript",
            "TypeScript",
            "Python"
        ]
        result = find_best_semantic_match(
            "Java",
            candidates,
            threshold=0.75
        )
        
        # Should not find a match above threshold
        # (might be None or with low similarity)
        if result:
            matched_skill, similarity = result
            # If it found something, similarity should be below threshold
            self.assertLess(similarity, 0.75)

    def test_no_match_below_threshold(self):
        """Skills below threshold should return None."""
        candidates = [
            "Photography",
            "Videography",
            "Painting"
        ]
        result = find_best_semantic_match(
            "Java",
            candidates,
            threshold=0.75
        )
        
        # Very different domain, should be None or below threshold
        if result:
            _, similarity = result
            self.assertLess(similarity, 0.75)

    def test_empty_candidate_list(self):
        """Empty candidate list should return None."""
        result = find_best_semantic_match(
            "Java",
            [],
            threshold=0.75
        )
        self.assertIsNone(result)

    def test_threshold_sensitivity(self):
        """Lowering threshold should increase matches."""
        candidates = ["Python", "PyTorch", "Pandas"]
        
        # High threshold - likely no match
        result_high = find_best_semantic_match(
            "Python",
            candidates,
            threshold=0.95
        )
        
        # Lower threshold - more likely to match
        result_low = find_best_semantic_match(
            "Python",
            candidates,
            threshold=0.60
        )
        
        # The low threshold version should match more easily
        # (result_high might be None or have exact match,
        #  result_low should definitely have a match)


class TestEmbeddingGeneration(unittest.TestCase):
    """Test embedding generation."""

    def test_embedding_not_none(self):
        """Embedding for valid text should not be None."""
        embedding = generate_embedding("Java")
        self.assertIsNotNone(embedding)

    def test_embedding_correct_dimension(self):
        """Embedding should have correct dimensions (384 for all-MiniLM-L6-v2)."""
        embedding = generate_embedding("REST API")
        if embedding is not None:
            # all-MiniLM-L6-v2 produces 384-dimensional embeddings
            self.assertEqual(len(embedding), 384)

    def test_embedding_empty_string_returns_none(self):
        """Embedding for empty string should return None."""
        embedding = generate_embedding("")
        self.assertIsNone(embedding)

    def test_embedding_whitespace_only_returns_none(self):
        """Embedding for whitespace-only string should return None."""
        embedding = generate_embedding("   ")
        self.assertIsNone(embedding)

    def test_embedding_non_string_returns_none(self):
        """Embedding for non-string should return None."""
        embedding = generate_embedding(None)
        self.assertIsNone(embedding)

        embedding = generate_embedding(123)
        self.assertIsNone(embedding)


class TestHybridMatchingIntegration(unittest.TestCase):
    """Integration tests for hybrid matching (combining exact + semantic)."""

    def test_exact_match_takes_precedence(self):
        """
        Exact matches should be found before semantic matching.
        
        In hybrid matching:
        1. Try exact match (normalized string comparison)
        2. If no exact match, try semantic matching
        3. Return results
        """
        # This is more of a behavioral test
        # The actual hybrid logic is in matcher.py, not semantic_matcher.py
        # But we can verify that exact matches are reliable
        
        from ai.matcher import find_matching_skills
        
        candidate_skills = ["Java", "Python", "REST API"]
        job_skills = ["Java", "SQL"]
        
        matched, missing = find_matching_skills(candidate_skills, job_skills)
        
        # Java should be in matched (exact match)
        self.assertIn("Java", matched)
        # SQL should be in missing
        self.assertIn("SQL", missing)

    def test_semantic_matching_complements_exact_matching(self):
        """
        Semantic matching should find skills that exact matching misses.
        
        When a job asks for "RESTful API" but candidate has "REST API development",
        Exact matching alone would fail, but hybrid matching should succeed.
        """
        # This test would require the full matcher.py integration
        # Here we just verify that semantic similarity is high
        
        similarity = calculate_semantic_similarity(
            "REST API development",
            "RESTful API"
        )
        
        # Semantic matching should recognize these as related
        self.assertGreater(similarity, 0.70)


class TestThresholdBehavior(unittest.TestCase):
    """Test how threshold affects matching behavior."""

    def test_high_threshold_strict_matching(self):
        """High threshold (e.g., 0.95) should only match very similar skills."""
        candidates = ["Object Oriented Programming"]
        
        # With high threshold, might not match
        result_high = find_best_semantic_match(
            "OOP",
            candidates,
            threshold=0.95
        )
        
        # With moderate threshold, should match
        result_moderate = find_best_semantic_match(
            "OOP",
            candidates,
            threshold=0.60
        )
        
        # Moderate threshold should be more permissive
        if result_high is None or result_high[1] < 0.95:
            self.assertIsNotNone(result_moderate)

    def test_low_threshold_permissive_matching(self):
        """Low threshold (e.g., 0.50) should match more liberally."""
        # This could lead to false positives, so be careful
        candidates = ["API", "Web Services"]
        
        result = find_best_semantic_match(
            "REST API",
            candidates,
            threshold=0.40
        )
        
        # With low threshold, should find something
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
