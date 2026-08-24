"""Generate personalized interview questions from analyzed candidate and job data."""

import json
import re
from typing import Any, Dict, Optional

ALLOWED_INTERVIEW_TYPES = {"technical", "hr", "behavioral", "mixed"}
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
ALLOWED_QUESTION_COUNTS = {5, 10, 15}
REQUIRED_QUESTION_FIELDS = {"question", "category", "difficulty", "topic", "reason"}
ALLOWED_CATEGORIES = {"technical", "hr", "behavioral"}


class QuestionGenerator:
    """Use an already-configured OpenAI client to generate interview questions."""

    def __init__(self, client: Any, model: str):
        self.client = client
        self.model = model

    def generate(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        match_data: Dict[str, Any],
        interview_type: str,
        difficulty: str,
        number_of_questions: int,
    ) -> Dict[str, Any]:
        validation_error = validate_generation_inputs(
            resume_data,
            job_data,
            match_data,
            interview_type,
            difficulty,
            number_of_questions,
        )
        if validation_error:
            return {"success": False, "error": validation_error}

        prompt = build_prompt(
            resume_data,
            job_data,
            match_data,
            interview_type,
            difficulty,
            number_of_questions,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an interview preparation coach. Generate questions "
                            "using only the supplied candidate and job facts. Never claim "
                            "the candidate has a missing skill or an unlisted technology. "
                            "Return only valid JSON with a questions array. Avoid duplicates."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2200,
            )
            if not response.choices:
                return {"success": False, "error": "No questions were returned by the AI service."}

            content = response.choices[0].message.content or ""
            parsed = parse_json_response(content)
            validated = validate_question_response(
                parsed, difficulty, number_of_questions
            )
            if validated is None:
                return {"success": False, "error": "AI returned invalid question data."}

            return {"success": True, "questions": validated}
        except Exception:
            return {
                "success": False,
                "error": "Unable to generate interview questions right now. Please try again.",
            }


def validate_generation_inputs(
    resume_data: Any,
    job_data: Any,
    match_data: Any,
    interview_type: Any,
    difficulty: Any,
    number_of_questions: Any,
) -> Optional[str]:
    """Return a user-safe validation error, or None when inputs are valid."""
    if not isinstance(resume_data, dict) or not resume_data:
        return "Resume analysis is unavailable. Please analyze your resume first."
    if not isinstance(job_data, dict) or not job_data:
        return "Job analysis is unavailable. Please analyze the job description first."
    if not isinstance(match_data, dict) or not match_data:
        return "Resume-job matching is unavailable. Please match your resume to the job first."
    if interview_type not in ALLOWED_INTERVIEW_TYPES:
        return "Invalid interview type. Choose technical, hr, behavioral, or mixed."
    if difficulty not in ALLOWED_DIFFICULTIES:
        return "Invalid difficulty. Choose easy, medium, or hard."
    if number_of_questions not in ALLOWED_QUESTION_COUNTS:
        return "Invalid question count. Choose 5, 10, or 15 questions."
    return None


def build_prompt(
    resume_data: Dict[str, Any],
    job_data: Dict[str, Any],
    match_data: Dict[str, Any],
    interview_type: str,
    difficulty: str,
    number_of_questions: int,
) -> str:
    """Build a compact prompt from structured analysis rather than raw documents."""
    context = {
        "candidate": {
            "skills": resume_data.get("skills", []),
            "projects": resume_data.get("projects", []),
            "experience": resume_data.get("experience", []),
            "certifications": resume_data.get("certifications", []),
            "education": resume_data.get("education", []),
        },
        "job": {
            "title": job_data.get("job_title", "Not mentioned"),
            "required_skills": job_data.get("required_skills", []),
            "preferred_skills": job_data.get("preferred_skills", []),
            "responsibilities": job_data.get("responsibilities", []),
            "qualifications": job_data.get("qualifications", []),
        },
        "matching": {
            "matched_required_skills": match_data.get("matched_required_skills", []),
            "missing_required_skills": match_data.get("missing_required_skills", []),
            "missing_preferred_skills": match_data.get("missing_preferred_skills", []),
            "semantic_matches": match_data.get("semantic_matches", []),
        },
    }
    difficulty_rules = {
        "easy": "Ask fundamental concepts and straightforward questions.",
        "medium": "Ask conceptual, implementation, and project-based questions.",
        "hard": "Ask deep reasoning, architecture, optimization, trade-off, and challenging scenario questions.",
    }
    return (
        f"Generate exactly {number_of_questions} unique questions for a {interview_type} "
        f"interview at {difficulty} difficulty. {difficulty_rules[difficulty]}\n"
        "For technical questions, cover relevant technologies, projects, and missing skills "
        "as knowledge checks. For HR questions, cover motivation, strengths, goals, teamwork, "
        "and conflict. For behavioral questions, use scenarios. For mixed, balance categories.\n"
        "Each item must have exactly these string fields: question, category, difficulty, topic, reason. "
        "Use category values Technical, HR, or Behavioral and set difficulty to the requested value. "
        "A reason must identify the supplied context behind the question. Return only JSON.\n\n"
        f"CONTEXT:\n{json.dumps(context, ensure_ascii=True)}"
    )


def parse_json_response(content: str) -> Optional[Dict[str, Any]]:
    """Parse JSON, tolerating a surrounding Markdown code fence or prose."""
    if not isinstance(content, str) or not content.strip():
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def validate_question_response(
    response: Any, difficulty: str, number_of_questions: int
) -> Optional[list[Dict[str, str]]]:
    """Validate the model contract and remove duplicate questions."""
    if not isinstance(response, dict) or not isinstance(response.get("questions"), list):
        return None
    questions = []
    seen = set()
    for item in response["questions"]:
        if not isinstance(item, dict) or set(item) != REQUIRED_QUESTION_FIELDS:
            return None
        if any(not isinstance(item[field], str) or not item[field].strip() for field in REQUIRED_QUESTION_FIELDS):
            return None
        if item["difficulty"].strip().lower() != difficulty:
            return None
        if item["category"].strip().lower() not in ALLOWED_CATEGORIES:
            return None
        key = re.sub(r"\s+", " ", item["question"].strip().lower())
        if key in seen:
            return None
        seen.add(key)
        questions.append({field: item[field].strip() for field in REQUIRED_QUESTION_FIELDS})
    if len(questions) != number_of_questions:
        return None
    return questions


def get_question_generator() -> Optional[QuestionGenerator]:
    """Reuse the existing analyzer's configured client and model."""
    from ai.resume_analyzer import get_analyzer

    analyzer = get_analyzer()
    if not analyzer:
        return None
    return QuestionGenerator(analyzer.client, analyzer.model)


def generate_interview_questions(
    resume_data: Dict[str, Any],
    job_data: Dict[str, Any],
    match_data: Dict[str, Any],
    interview_type: str,
    difficulty: str,
    number_of_questions: int,
) -> Dict[str, Any]:
    """Public function used by Flask and tests."""
    validation_error = validate_generation_inputs(
        resume_data, job_data, match_data, interview_type, difficulty, number_of_questions
    )
    if validation_error:
        return {"success": False, "error": validation_error}
    generator = get_question_generator()
    if not generator:
        return {"success": False, "error": "AI service is not configured. Please set OPENAI_API_KEY."}
    return generator.generate(
        resume_data, job_data, match_data, interview_type, difficulty, number_of_questions
    )
