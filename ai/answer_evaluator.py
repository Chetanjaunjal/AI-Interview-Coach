"""Evaluate one interview answer with a validated rubric and deterministic scoring."""

import json
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional


ALLOWED_CATEGORIES = {"technical", "hr", "behavioral"}
SCORE_FIELDS = {"relevance", "completeness", "communication"}
TECHNICAL_WEIGHTS = {
    "relevance": 0.25,
    "technical_correctness": 0.35,
    "completeness": 0.25,
    "communication": 0.15,
}
CONTENT_WEIGHTS = {
    "relevance": 0.25,
    "content_quality": 0.35,
    "completeness": 0.25,
    "communication": 0.15,
}
FEEDBACK_FIELDS = {
    "strengths",
    "weaknesses",
    "missing_points",
    "improvement_suggestions",
    "model_feedback",
}


class AnswerEvaluator:
    """Use an existing configured LLM client to evaluate a single answer."""

    def __init__(self, client: Any, model: str):
        self.client = client
        self.model = model

    def evaluate(
        self,
        question: str,
        answer: str,
        category: str,
        difficulty: str,
        topic: str,
        job_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        validation_error = validate_evaluation_inputs(
            question, answer, category, difficulty, topic
        )
        if validation_error:
            return {"success": False, "error": validation_error}

        prompt = build_evaluation_prompt(
            question, answer, category, difficulty, topic, job_context or {}
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a fair interview evaluator. Evaluate only the supplied "
                            "question and answer. Accept correct alternative explanations, "
                            "do not invent candidate facts, and give constructive feedback. "
                            "Return only valid JSON with the requested rubric fields."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1400,
            )
            if not response.choices:
                return {"success": False, "error": "No evaluation was returned by the AI service."}
            parsed = parse_json_response(response.choices[0].message.content or "")
            evaluation = validate_and_score_evaluation(parsed, category)
            if evaluation is None:
                return {"success": False, "error": "AI returned invalid evaluation data."}
            return {"success": True, "evaluation": evaluation}
        except Exception:
            return {
                "success": False,
                "error": "The AI service is temporarily unavailable. Please continue without evaluation.",
            }


def validate_evaluation_inputs(
    question: Any, answer: Any, category: Any, difficulty: Any, topic: Any
) -> Optional[str]:
    """Validate the data sent to the evaluator."""
    if not isinstance(question, str) or not question.strip():
        return "The interview question is missing."
    if not isinstance(answer, str) or not answer.strip():
        return "Please provide an answer before evaluation."
    if not isinstance(category, str) or category.strip().lower() not in ALLOWED_CATEGORIES:
        return "The interview question category is invalid."
    if not isinstance(difficulty, str) or not difficulty.strip():
        return "The interview question difficulty is missing."
    if not isinstance(topic, str) or not topic.strip():
        return "The interview question topic is missing."
    return None


def build_evaluation_prompt(
    question: str,
    answer: str,
    category: str,
    difficulty: str,
    topic: str,
    job_context: Dict[str, Any],
) -> str:
    """Build a compact, category-aware rubric prompt."""
    normalized_category = category.strip().lower()
    criterion = "technical_correctness" if normalized_category == "technical" else "content_quality"
    category_rules = {
        "technical": "Prioritize technical correctness. Identify incorrect claims and missing concepts.",
        "hr": "Use content quality instead of technical correctness. Evaluate motivation, self-awareness, and role relevance.",
        "behavioral": "Use content quality instead of technical correctness. Consider relevance, clarity, and helpful Situation, Task, Action, and Result details without requiring STAR.",
    }
    context = {
        "required_skills": job_context.get("required_skills", []),
        "preferred_skills": job_context.get("preferred_skills", []),
        "responsibilities": job_context.get("responsibilities", []),
        "qualifications": job_context.get("qualifications", []),
    }
    return (
        f"Evaluate this {normalized_category} interview answer at {difficulty} difficulty. "
        f"{category_rules[normalized_category]}\n"
        "Score every criterion from 0 to 10. Do not judge exact wording; accept technically "
        "correct alternatives. Treat a short answer as incomplete when it lacks important detail, "
        "but explain how to improve it constructively. Return only JSON with exactly these fields: "
        f"relevance, {criterion}, completeness, communication, strengths, weaknesses, "
        "missing_points, improvement_suggestions, model_feedback. Score fields must be numbers "
        "from 0 through 10; feedback fields must be arrays of strings except model_feedback, which "
        "must be a string.\n\n"
        f"Question: {question}\nAnswer: {answer}\nCategory: {category}\nDifficulty: {difficulty}\n"
        f"Topic: {topic}\nRelevant job context: {json.dumps(context, ensure_ascii=True)}"
    )


def parse_json_response(content: str) -> Optional[Dict[str, Any]]:
    """Parse direct JSON or JSON surrounded by a code fence/prose."""
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


def validate_and_score_evaluation(
    response: Any, category: str, weights: Optional[Dict[str, float]] = None
) -> Optional[Dict[str, Any]]:
    """Validate model rubric fields and calculate the overall score in Python."""
    if not isinstance(response, dict):
        return None
    normalized_category = category.strip().lower()
    correctness_field = "technical_correctness" if normalized_category == "technical" else "content_quality"
    score_fields = SCORE_FIELDS | {correctness_field}
    required_fields = score_fields | FEEDBACK_FIELDS
    if set(response) != required_fields:
        return None

    for field in score_fields:
        value = response.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 10:
            return None
    for field in FEEDBACK_FIELDS - {"model_feedback"}:
        if not isinstance(response[field], list) or any(
            not isinstance(item, str) or not item.strip() for item in response[field]
        ):
            return None
    if not isinstance(response["model_feedback"], str) or not response["model_feedback"].strip():
        return None

    selected_weights = weights or (TECHNICAL_WEIGHTS if normalized_category == "technical" else CONTENT_WEIGHTS)
    if set(selected_weights) != score_fields or abs(sum(selected_weights.values()) - 1.0) > 0.001:
        return None
    score_order = (
        ("relevance", "technical_correctness", "completeness", "communication")
        if normalized_category == "technical"
        else ("relevance", "content_quality", "completeness", "communication")
    )
    overall_decimal = sum(
        Decimal(str(response[field])) * Decimal(str(selected_weights[field]))
        for field in score_order
    )
    overall = float(overall_decimal.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    result = {field: response[field] for field in required_fields}
    result["overall_score"] = overall
    return result


def get_answer_evaluator() -> Optional[AnswerEvaluator]:
    """Reuse the existing analyzer's API client and model configuration."""
    from ai.resume_analyzer import get_analyzer

    analyzer = get_analyzer()
    if not analyzer:
        return None
    return AnswerEvaluator(analyzer.client, analyzer.model)


def evaluate_answer(
    question: str,
    answer: str,
    category: str,
    difficulty: str,
    topic: str,
    job_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Public evaluator function used by Flask and tests."""
    validation_error = validate_evaluation_inputs(question, answer, category, difficulty, topic)
    if validation_error:
        return {"success": False, "error": validation_error}
    evaluator = get_answer_evaluator()
    if not evaluator:
        return {"success": False, "error": "AI service is not configured. Please set OPENAI_API_KEY."}
    return evaluator.evaluate(question, answer, category, difficulty, topic, job_context)
