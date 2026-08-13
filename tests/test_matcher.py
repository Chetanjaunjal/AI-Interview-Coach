"""
Test cases for the Resume-Job Matching System (Commit #6)

This test file demonstrates:
1. Strong match between resume and job
2. Partial match with missing skills
3. No match scenario
4. Case-insensitive matching
5. Java vs JavaScript distinction
6. No preferred skills handling
7. Empty skill lists handling

Run with: python -m pytest tests/test_matcher.py -v
Or: python -m unittest tests.test_matcher -v
"""

import unittest
from ai.matcher import (
    normalize_skill,
    extract_skills_from_analysis,
    find_matching_skills,
    calculate_match_percentage,
    generate_recommendations,
    match_resume_to_job,
)


class TestSkillNormalization(unittest.TestCase):
    """Test the skill normalization function."""

    def test_normalize_lowercase(self):
        """Test normalization converts to lowercase."""
        self.assertEqual(normalize_skill("Java"), "java")
        self.assertEqual(normalize_skill("PYTHON"), "python")
        self.assertEqual(normalize_skill("SQL"), "sql")

    def test_normalize_whitespace(self):
        """Test normalization removes leading/trailing whitespace."""
        self.assertEqual(normalize_skill("  Java  "), "java")
        self.assertEqual(normalize_skill(" Spring Boot "), "spring boot")
        self.assertEqual(normalize_skill("\tPython\n"), "python")

    def test_normalize_combined(self):
        """Test normalization handles combined case and whitespace."""
        self.assertEqual(normalize_skill("  JAVA  "), "java")
        self.assertEqual(normalize_skill("  Spring Boot  "), "spring boot")

    def test_normalize_empty_string(self):
        """Test normalization of empty string."""
        self.assertEqual(normalize_skill(""), "")

    def test_normalize_special_characters(self):
        """Test normalization preserves special characters (like C++)."""
        self.assertEqual(normalize_skill("C++"), "c++")
        self.assertEqual(normalize_skill("C#"), "c#")
        self.assertEqual(normalize_skill("Node.js"), "node.js")


class TestFindMatchingSkills(unittest.TestCase):
    """Test the skill matching logic."""

    def test_exact_match(self):
        """Test finding exact skill matches."""
        candidate = ["Java", "Python", "SQL"]
        job = ["Java", "Python", "SQL"]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(sorted(matched), ["Java", "Python", "SQL"])
        self.assertEqual(missing, [])

    def test_case_insensitive_match(self):
        """Test that matching is case-insensitive."""
        candidate = ["Java", "Python"]
        job = ["java", "python"]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(sorted(matched), ["Java", "Python"])
        self.assertEqual(missing, [])

    def test_whitespace_insensitive_match(self):
        """Test that matching handles whitespace differences."""
        candidate = ["Spring Boot", "Docker"]
        job = [" spring boot ", "  docker  "]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(sorted(matched), ["Docker", "Spring Boot"])
        self.assertEqual(missing, [])

    def test_partial_match(self):
        """Test partial skill matching."""
        candidate = ["Java", "Python"]
        job = ["Java", "Python", "Spring Boot"]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(sorted(matched), ["Java", "Python"])
        self.assertEqual(missing, ["Spring Boot"])

    def test_no_match(self):
        """Test when there are no matching skills."""
        candidate = ["Python", "Django"]
        job = ["Java", "Spring Boot"]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(matched, [])
        self.assertEqual(sorted(missing), ["Java", "Spring Boot"])

    def test_java_vs_javascript_not_matched(self):
        """Test that Java and JavaScript are treated as different skills."""
        candidate = ["Java"]
        job = ["JavaScript"]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(matched, [])
        self.assertEqual(missing, ["JavaScript"])

    def test_react_vs_react_native_not_matched(self):
        """Test that React and React Native are treated as different skills."""
        candidate = ["React"]
        job = ["React Native"]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(matched, [])
        self.assertEqual(missing, ["React Native"])

    def test_empty_candidate_skills(self):
        """Test matching with empty candidate skills."""
        candidate = []
        job = ["Java", "SQL"]

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(matched, [])
        self.assertEqual(sorted(missing), ["Java", "SQL"])

    def test_empty_job_skills(self):
        """Test matching with empty job skills."""
        candidate = ["Java", "SQL"]
        job = []

        matched, missing = find_matching_skills(candidate, job)

        self.assertEqual(matched, [])
        self.assertEqual(missing, [])


class TestMatchPercentageCalculation(unittest.TestCase):
    """Test match percentage calculation."""

    def test_perfect_match(self):
        """Test perfect match (100%)."""
        # All required skills matched, all preferred matched
        percentage = calculate_match_percentage(
            matched_required=2,
            total_required=2,
            matched_preferred=2,
            total_preferred=2
        )
        self.assertEqual(percentage, 100)

    def test_all_required_no_preferred(self):
        """Test when all required skills match, no preferred skills."""
        # 2/2 required matched, 0/2 preferred matched
        percentage = calculate_match_percentage(
            matched_required=2,
            total_required=2,
            matched_preferred=0,
            total_preferred=2
        )
        self.assertEqual(percentage, 70)

    def test_no_required_all_preferred(self):
        """Test when no required skills match, but all preferred do."""
        # 0/2 required matched, 2/2 preferred matched
        percentage = calculate_match_percentage(
            matched_required=0,
            total_required=2,
            matched_preferred=2,
            total_preferred=2
        )
        self.assertEqual(percentage, 30)

    def test_partial_required_partial_preferred(self):
        """Test partial matches on both required and preferred."""
        # 2/4 required (50%), 1/2 preferred (50%)
        percentage = calculate_match_percentage(
            matched_required=2,
            total_required=4,
            matched_preferred=1,
            total_preferred=2
        )
        # (0.5 * 0.70) + (0.5 * 0.30) = 0.35 + 0.15 = 0.50 = 50%
        self.assertEqual(percentage, 50)

    def test_no_skills_required_some_preferred(self):
        """Test when job has no required skills, only preferred."""
        # 0 required (no required dimension), 1/2 preferred
        percentage = calculate_match_percentage(
            matched_required=0,
            total_required=0,
            matched_preferred=1,
            total_preferred=2
        )
        # Only preferred dimension exists: 1/2 = 50%
        self.assertEqual(percentage, 50)

    def test_some_required_no_preferred(self):
        """Test when job has required skills but no preferred."""
        # 1/2 required, no preferred dimension
        percentage = calculate_match_percentage(
            matched_required=1,
            total_required=2,
            matched_preferred=0,
            total_preferred=0
        )
        # Only required dimension exists: 1/2 = 50%
        self.assertEqual(percentage, 50)

    def test_zero_skills(self):
        """Test when there are no skills at all."""
        percentage = calculate_match_percentage(
            matched_required=0,
            total_required=0,
            matched_preferred=0,
            total_preferred=0
        )
        self.assertEqual(percentage, 100)

    def test_no_match_at_all(self):
        """Test when nothing matches."""
        percentage = calculate_match_percentage(
            matched_required=0,
            total_required=5,
            matched_preferred=0,
            total_preferred=5
        )
        self.assertEqual(percentage, 0)


class TestRecommendationGeneration(unittest.TestCase):
    """Test recommendation generation."""

    def test_recommendations_for_missing_required(self):
        """Test recommendations for missing required skills."""
        recs = generate_recommendations(
            matched_required=["Java"],
            missing_required=["Spring Boot", "Data Structures"],
            missing_preferred=[]
        )

        self.assertIn("Learn Spring Boot - this is critical for the role", recs)
        self.assertIn("Learn Data Structures - this is critical for the role", recs)

    def test_recommendations_for_missing_preferred(self):
        """Test recommendations for missing preferred skills."""
        recs = generate_recommendations(
            matched_required=["Java", "SQL"],
            missing_required=[],
            missing_preferred=["Docker", "AWS"]
        )

        self.assertIn("Great! You have all required skills", recs[0])
        self.assertIn("Docker knowledge would strengthen your profile", recs)

    def test_recommendations_all_skills_present(self):
        """Test recommendations when all skills are present."""
        recs = generate_recommendations(
            matched_required=["Java", "SQL"],
            missing_required=[],
            missing_preferred=[]
        )

        self.assertEqual(len(recs), 1)
        self.assertIn("Excellent!", recs[0])

    def test_recommendations_limited_to_three_preferred(self):
        """Test that preferred skill recommendations are limited to 3."""
        recs = generate_recommendations(
            matched_required=["Java"],
            missing_required=["Spring Boot"],
            missing_preferred=["Docker", "AWS", "Kubernetes", "Terraform"]
        )

        # Should have 1 for Spring Boot + max 3 for preferred
        self.assertLessEqual(len(recs), 4)


class TestFullMatchingFlow(unittest.TestCase):
    """Test the complete matching flow."""

    def test_strong_match_scenario(self):
        """
        Test Case 1: Strong match between resume and job.
        
        Resume: Java, SQL, Git, HTML, CSS, Python
        Job Required: Java, SQL, Git
        Job Preferred: Docker, AWS
        
        Expected: Very high match (>80%)
        """
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java", "SQL", "Git", "HTML", "CSS", "Python"]
            }
        }

        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java", "SQL", "Git"],
                "preferred_skills": ["Docker", "AWS"]
            }
        }

        result = match_resume_to_job(resume_analysis, job_analysis)

        self.assertTrue(result["success"])
        matching = result["result"]
        
        # All required skills matched
        self.assertEqual(len(matching["matched_required_skills"]), 3)
        self.assertEqual(len(matching["missing_required_skills"]), 0)
        
        # No preferred skills matched
        self.assertEqual(len(matching["matched_preferred_skills"]), 0)
        self.assertEqual(len(matching["missing_preferred_skills"]), 2)
        
        # Extra skills present
        self.assertEqual(len(matching["additional_candidate_skills"]), 3)
        
        # Match score should be 70% (100% required, 0% preferred)
        self.assertEqual(matching["match_percentage"], 70)

    def test_partial_match_scenario(self):
        """
        Test Case 2: Partial match with missing skills.
        
        Resume: Java, SQL
        Job Required: Java, SQL, Spring Boot, Data Structures
        Job Preferred: Docker, AWS
        
        Expected: Partial match around 35%
        """
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java", "SQL"]
            }
        }

        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java", "SQL", "Spring Boot", "Data Structures"],
                "preferred_skills": ["Docker", "AWS"]
            }
        }

        result = match_resume_to_job(resume_analysis, job_analysis)

        self.assertTrue(result["success"])
        matching = result["result"]
        
        # 2 of 4 required matched (50%)
        self.assertEqual(len(matching["matched_required_skills"]), 2)
        self.assertEqual(len(matching["missing_required_skills"]), 2)
        
        # 0 of 2 preferred matched
        self.assertEqual(len(matching["matched_preferred_skills"]), 0)
        self.assertEqual(len(matching["missing_preferred_skills"]), 2)
        
        # Match score should be ~35% (50% required * 0.70 + 0% preferred * 0.30)
        self.assertEqual(matching["match_percentage"], 35)

    def test_no_match_scenario(self):
        """
        Test Case 3: No match scenario.
        
        Resume: Python, Django
        Job Required: Java, Spring Boot
        
        Expected: Very low match (~0%)
        """
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Python", "Django"]
            }
        }

        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java", "Spring Boot"],
                "preferred_skills": []
            }
        }

        result = match_resume_to_job(resume_analysis, job_analysis)

        self.assertTrue(result["success"])
        matching = result["result"]
        
        # No required skills matched
        self.assertEqual(len(matching["matched_required_skills"]), 0)
        self.assertEqual(len(matching["missing_required_skills"]), 2)
        
        # Match score should be 0%
        self.assertEqual(matching["match_percentage"], 0)

    def test_case_insensitive_matching(self):
        """
        Test Case 4: Case-insensitive matching.
        
        Resume: Java, SQL
        Job Required: JAVA, sql
        
        Expected: They should match (100% match)
        """
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java", "SQL"]
            }
        }

        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["JAVA", "sql"],
                "preferred_skills": []
            }
        }

        result = match_resume_to_job(resume_analysis, job_analysis)

        self.assertTrue(result["success"])
        matching = result["result"]
        
        # Both should match despite case differences
        self.assertEqual(len(matching["matched_required_skills"]), 2)
        self.assertEqual(matching["match_percentage"], 100)

    def test_java_vs_javascript(self):
        """
        Test Case 5: Java vs JavaScript must NOT be treated as same.
        
        Resume: Java
        Job Required: JavaScript
        
        Expected: No match (0%)
        """
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java"]
            }
        }

        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["JavaScript"],
                "preferred_skills": []
            }
        }

        result = match_resume_to_job(resume_analysis, job_analysis)

        self.assertTrue(result["success"])
        matching = result["result"]
        
        # Java should NOT match JavaScript
        self.assertEqual(len(matching["matched_required_skills"]), 0)
        self.assertEqual(len(matching["missing_required_skills"]), 1)
        self.assertEqual(matching["match_percentage"], 0)

    def test_no_preferred_skills(self):
        """
        Test Case 6: Job has only required skills, no preferred.
        
        Resume: Java, SQL, Git
        Job Required: Java, SQL
        Job Preferred: (none)
        
        Expected: 100% match
        """
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java", "SQL", "Git"]
            }
        }

        job_analysis = {
            "success": True,
            "analysis": {
                "required_skills": ["Java", "SQL"],
                "preferred_skills": []
            }
        }

        result = match_resume_to_job(resume_analysis, job_analysis)

        self.assertTrue(result["success"])
        matching = result["result"]
        
        # All required matched, no preferred to match
        self.assertEqual(matching["match_percentage"], 100)

    def test_error_missing_resume_analysis(self):
        """Test Case 7: Error when resume analysis is missing."""
        resume_analysis = {
            "success": False,
            "error": "Failed to analyze"
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
        self.assertIn("error", result)

    def test_error_missing_job_analysis(self):
        """Test Case 8: Error when job analysis is missing."""
        resume_analysis = {
            "success": True,
            "analysis": {
                "skills": ["Java"]
            }
        }

        job_analysis = {
            "success": False,
            "error": "Failed to analyze"
        }

        result = match_resume_to_job(resume_analysis, job_analysis)

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_error_empty_candidate_skills(self):
        """Test Case 9: Error when resume has no skills."""
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
        self.assertIn("error", result)

    def test_error_empty_job_skills(self):
        """Test Case 10: Error when job has no skills."""
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
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
