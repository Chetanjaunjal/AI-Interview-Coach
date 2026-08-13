"""
Resume-Job Matching Module

This module implements transparent, explainable skill matching between
a candidate's resume and a job description.

Key principles:
1. Deterministic: Same input always produces same output (no randomness)
2. Explainable: Every match decision can be traced back to specific skills
3. Transparent: Uses simple string comparison (normalized), not "black box" AI
4. Modular: Can be tested independently from Flask

Why deterministic over AI?
- Faster: No LLM API calls
- Cheaper: No token usage for matching
- Debuggable: We can explain exactly why a skill matched/didn't match
- Reproducible: Results don't vary randomly
- Explainable: Users see the reasoning

Limitations:
- We treat "Java" and "JavaScript" as completely different (good - prevents false matches)
- We don't understand skill dependencies ("Java" doesn't imply "OOP")
- We don't account for skill levels ("1 year Java" vs "10 years Java")
- We don't handle synonyms ("REST API" vs "Web API")

These limitations are intentional for Commit #6. We can add semantic matching
and embeddings in a future commit.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class MatchResult:
    """Structured result from resume-job matching."""
    match_percentage: int  # 0-100
    matched_required_skills: List[str]
    missing_required_skills: List[str]
    matched_preferred_skills: List[str]
    missing_preferred_skills: List[str]
    additional_candidate_skills: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill name to a standard form for comparison.

    Normalization rules:
    1. Strip leading/trailing whitespace
    2. Convert to lowercase

    Examples:
        "  Java  " → "java"
        "SQL" → "sql"
        "Python" → "python"
        " Spring Boot " → "spring boot"

    Why we normalize:
    - Resume might say "Java", job posting might say "java"
    - Different people write skills differently
    - Normalization ensures we catch all matches

    What we DON'T do (for Commit #6):
    - Remove punctuation: "C++" stays "c++" (correct - it's the language name)
    - Stemming: "running" → "run" (would lose meaning)
    - Lemmatization: too aggressive for tech skills
    - Semantic similarity: "Java" ≠ "JavaScript" (we want exact match)

    Args:
        skill: Raw skill string from resume or job analysis

    Returns:
        Normalized skill string in lowercase with whitespace trimmed
    """
    if not isinstance(skill, str):
        return ""

    return skill.strip().lower()


def extract_skills_from_analysis(analysis: Dict[str, Any]) -> List[str]:
    """
    Extract skills from AI analysis results.

    The AI analyzer returns a dictionary like:
    {
        "skills": ["Java", "Python", "SQL"],
        "education": [...],
        ...
    }

    This function safely extracts the skills list.

    Why a separate function?
    - Isolates skill extraction logic
    - Makes it easy to change AI response format
    - Handles missing/malformed data gracefully

    Args:
        analysis: Dictionary from resume_analyzer.py or job_analyzer.py

    Returns:
        List of skills (strings). Empty list if no skills found.
    """
    if not isinstance(analysis, dict):
        return []

    skills = analysis.get("skills", [])

    # Ensure we always return a list
    if not isinstance(skills, list):
        return []

    # Filter out empty strings and non-string values
    return [str(s).strip() for s in skills if s and isinstance(s, (str, int, float))]


def extract_required_skills(job_analysis: Dict[str, Any]) -> List[str]:
    """
    Extract required skills from job analysis.

    Args:
        job_analysis: Dictionary from job_analyzer.py

    Returns:
        List of required skills
    """
    if not isinstance(job_analysis, dict):
        return []

    required = job_analysis.get("required_skills", [])

    if not isinstance(required, list):
        return []

    return [str(s).strip() for s in required if s and isinstance(s, (str, int, float))]


def extract_preferred_skills(job_analysis: Dict[str, Any]) -> List[str]:
    """
    Extract preferred skills from job analysis.

    Args:
        job_analysis: Dictionary from job_analyzer.py

    Returns:
        List of preferred skills
    """
    if not isinstance(job_analysis, dict):
        return []

    preferred = job_analysis.get("preferred_skills", [])

    if not isinstance(preferred, list):
        return []

    return [str(s).strip() for s in preferred if s and isinstance(s, (str, int, float))]


def find_matching_skills(
    candidate_skills: List[str], job_skills: List[str]
) -> tuple[List[str], List[str]]:
    """
    Find which candidate skills match job skills.

    This is the core matching logic.

    Algorithm:
    1. Normalize all skills (lowercase, strip whitespace)
    2. Create a set of normalized job skills (for fast lookup)
    3. For each candidate skill, check if normalized version exists in job skills
    4. Return matched candidates and missing job skills

    Time complexity: O(n + m) where n=candidate skills, m=job skills
    (Fast enough for typical resume and job data)

    Why sets?
    - Set membership checking is O(1) - constant time
    - List membership checking is O(n) - linear time
    - For 50 skills, sets are ~50x faster

    Example:
        candidate_skills = ["Java", "Python", "SQL"]
        job_skills = ["Java", "sql", "Spring Boot"]

        Normalized:
        - candidate: {"java", "python", "sql"}
        - job: {"java", "sql", "spring boot"}

        Matched: ["Java", "SQL"] (from candidate)
        Missing: ["Spring Boot"] (from job)

    Args:
        candidate_skills: Skills from resume analysis
        job_skills: Required or preferred skills from job analysis

    Returns:
        Tuple of (matched_candidates, missing_job_skills)
        matched_candidates: Which candidate skills appear in job
        missing_job_skills: Which job skills don't appear in candidate resume
    """
    # Normalize all skills
    normalized_candidate_skills = [normalize_skill(s) for s in candidate_skills]
    normalized_job_skills = [normalize_skill(s) for s in job_skills]

    # Create a set for fast lookup
    normalized_candidate_set = set(normalized_candidate_skills)

    # Find matched skills (preserving original capitalization from candidate)
    matched = []
    for original, normalized in zip(candidate_skills, normalized_candidate_skills):
        if normalized in normalized_job_skills:
            matched.append(original)

    # Find missing skills (preserving original capitalization from job)
    missing = []
    for original, normalized in zip(job_skills, normalized_job_skills):
        if normalized not in normalized_candidate_set:
            missing.append(original)

    return matched, missing


def calculate_match_percentage(
    matched_required: int,
    total_required: int,
    matched_preferred: int,
    total_preferred: int,
) -> int:
    """
    Calculate overall match percentage using weighted scoring.

    Scoring formula:
    ----------------

    Required Score = matched_required / total_required  (if total_required > 0)
    Preferred Score = matched_preferred / total_preferred  (if total_preferred > 0)

    Overall Match % = (Required Score × 0.70) + (Preferred Score × 0.30)

    Why 70/30 weights?
    - Required skills are "must-haves" → higher weight
    - Preferred skills are "nice-to-haves" → lower weight
    - This matches hiring reality: required skills matter more
    - Example: A candidate with all required skills + 0 preferred should score
      higher than someone with 0 required + all preferred

    Edge cases:
    -----------

    Case 1: No required skills but has preferred skills
        → Only evaluate preferred dimension
        → Example: no required, 1/2 preferred → 50% (not 85%)

    Case 2: No preferred skills but has required skills
        → Only evaluate required dimension
        → Example: 1/2 required, no preferred → 50% (not 65%)

    Case 3: Both required and preferred exist
        → Use weighted 70/30 formula
        → Example: 1/2 required, 1/2 preferred → (50% × 0.70) + (50% × 0.30) = 50%

    Case 4: No candidate skills (resume has no skills)
        → Already caught before this function is called

    Case 5: No job requirements at all (no required or preferred)
        → This shouldn't happen (caught before calling this function)

    Why this approach:
    - An empty dimension (no skills specified) shouldn't give free points
    - If a job only specifies required skills, don't penalize for missing preferred
    - If a job only specifies preferred skills, evaluate only on those
    - Fair scoring regardless of how many skill categories a job uses

    Args:
        matched_required: Count of required skills candidate has
        total_required: Total count of required skills in job
        matched_preferred: Count of preferred skills candidate has
        total_preferred: Total count of preferred skills in job

    Returns:
        Integer 0-100 representing match percentage
    """
    # Edge case: No skills at all in job (should not happen normally)
    if total_required == 0 and total_preferred == 0:
        return 100  # Everything "matches" when there are no requirements

    # Calculate scores for each dimension (if it exists)
    required_score = matched_required / total_required if total_required > 0 else None
    preferred_score = matched_preferred / total_preferred if total_preferred > 0 else None

    # Determine overall score based on which dimensions have content
    if required_score is not None and preferred_score is not None:
        # Both dimensions exist: use weighted combination
        overall_score = (required_score * 0.70) + (preferred_score * 0.30)
    elif required_score is not None:
        # Only required dimension exists
        overall_score = required_score
    else:
        # Only preferred dimension exists
        overall_score = preferred_score

    # Convert to percentage and round
    percentage = int(overall_score * 100)

    # Ensure result is 0-100
    return max(0, min(100, percentage))


def generate_recommendations(
    matched_required: List[str],
    missing_required: List[str],
    missing_preferred: List[str],
) -> List[str]:
    """
    Generate personalized recommendations for the candidate.

    Recommendations prioritize:
    1. Missing required skills (critical gaps)
    2. Missing preferred skills (nice-to-have improvements)

    Why prioritize required?
    - Required skills are blockers; without them, you can't do the job
    - Preferred skills are bonus; nice to have, but not essential

    Example output:
    [
        "Learn Spring Boot - this is critical for the role",
        "Study Data Structures in depth",
        "AWS knowledge would strengthen your profile"
    ]

    Why generate recommendations?
    - Gives candidate actionable next steps
    - Shows them what to prioritize learning
    - Makes results more helpful than just a score

    Args:
        matched_required: Required skills the candidate has
        missing_required: Required skills they're missing
        missing_preferred: Preferred skills they're missing

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Prioritize missing required skills
    for skill in missing_required:
        if skill:
            recommendations.append(
                f"Learn {skill} - this is critical for the role"
            )

    # Then suggest preferred skills
    for skill in missing_preferred[:3]:  # Limit to top 3 to avoid overwhelming
        if skill:
            recommendations.append(
                f"{skill} knowledge would strengthen your profile"
            )

    # If they have everything required, give them encouragement
    if not missing_required and recommendations:
        recommendations.insert(
            0, "Great! You have all required skills. Focus on preferred skills."
        )

    # If they have everything, give clear message
    if not missing_required and not missing_preferred:
        recommendations = ["Excellent! You meet all requirements for this role."]

    return recommendations if recommendations else ["Review the skill gaps above."]


def match_resume_to_job(
    resume_analysis: Dict[str, Any], job_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main matching function. Compares resume to job requirements.

    This is the heart of Commit #6.

    High-level algorithm:
    1. Extract candidate skills from resume analysis
    2. Extract required skills from job analysis
    3. Extract preferred skills from job analysis
    4. Normalize and compare skills
    5. Calculate match percentage
    6. Generate recommendations
    7. Return structured results

    Why this approach?
    - Separation of concerns (each step is clear)
    - Easy to test (each step can be tested independently)
    - Easy to debug (we know exactly which step failed)
    - Easy to improve (add semantic matching later without changing structure)

    Args:
        resume_analysis: Dictionary from resume_analyzer.analyze_resume()
            Expected to have: {"success": True, "analysis": {"skills": [...]}}

        job_analysis: Dictionary from job_analyzer.analyze_job_description()
            Expected to have: {"success": True, "analysis": {"required_skills": [...], "preferred_skills": [...]}}

    Returns:
        Dictionary with keys:
        - "success": True/False
        - "error": Error message (if success=False)
        - "result": MatchResult (if success=True)
    """

    # Input validation
    if not isinstance(resume_analysis, dict):
        return {
            "success": False,
            "error": "Resume analysis data is missing or invalid"
        }

    if not isinstance(job_analysis, dict):
        return {
            "success": False,
            "error": "Job analysis data is missing or invalid"
        }

    # Check if analyses were successful
    if not resume_analysis.get("success"):
        return {
            "success": False,
            "error": "Resume has not been analyzed yet. Please analyze your resume first."
        }

    if not job_analysis.get("success"):
        return {
            "success": False,
            "error": "Job description has not been analyzed yet. Please analyze the job description first."
        }

    # Extract analysis results
    resume_data = resume_analysis.get("analysis", {})
    job_data = job_analysis.get("analysis", {})

    # Step 1: Extract skills from analyses
    candidate_skills = extract_skills_from_analysis(resume_data)
    required_skills = extract_required_skills(job_data)
    preferred_skills = extract_preferred_skills(job_data)

    # Step 2: Check for empty skill lists
    if not candidate_skills:
        return {
            "success": False,
            "error": "No skills found in resume analysis. Please ensure your resume was analyzed correctly."
        }

    if not required_skills and not preferred_skills:
        return {
            "success": False,
            "error": "No skills found in job analysis. Please ensure the job description was analyzed correctly."
        }

    # Step 3: Find matches
    matched_required, missing_required = find_matching_skills(
        candidate_skills, required_skills
    )
    matched_preferred, missing_preferred = find_matching_skills(
        candidate_skills, preferred_skills
    )

    # Step 4: Find additional candidate skills (those not in job requirements)
    normalized_job_skills = set(normalize_skill(s) for s in required_skills + preferred_skills)
    additional_skills = [
        s for s in candidate_skills
        if normalize_skill(s) not in normalized_job_skills
    ]

    # Step 5: Calculate match percentage
    match_percentage = calculate_match_percentage(
        len(matched_required),
        len(required_skills),
        len(matched_preferred),
        len(preferred_skills),
    )

    # Step 6: Generate recommendations
    recommendations = generate_recommendations(
        matched_required, missing_required, missing_preferred
    )

    # Step 7: Create result
    result = MatchResult(
        match_percentage=match_percentage,
        matched_required_skills=matched_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=matched_preferred,
        missing_preferred_skills=missing_preferred,
        additional_candidate_skills=additional_skills,
        recommendations=recommendations,
    )

    return {
        "success": True,
        "result": result.to_dict()
    }
