"""Deterministic aggregation for a completed interview session."""

from collections import defaultdict
from typing import Any, Dict, Iterable, Optional


DEFAULT_STRONG_THRESHOLD = 8.0
DEFAULT_WEAK_THRESHOLD = 6.0
DEFAULT_MIN_TOPIC_QUESTIONS = 2
COMMON_METRICS = ("relevance", "completeness", "communication")


def _valid_score(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 10


def _score_values(evaluations: Iterable[Dict[str, Any]], field: str) -> list[float]:
    return [
        float(item[field])
        for item in evaluations
        if isinstance(item, dict) and _valid_score(item.get(field))
    ]


def _average(values: list[float]) -> Optional[float]:
    return round(sum(values) / len(values), 1) if values else None


def _evaluation_records(answers: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    records = []
    for answer in answers:
        if not isinstance(answer, dict) or not isinstance(answer.get("evaluation"), dict):
            continue
        evaluation = answer["evaluation"]
        if _valid_score(evaluation.get("overall_score")):
            records.append({
                "evaluation": evaluation,
                "category": str(answer.get("category", "")).strip(),
                "topic": str(answer.get("topic", "")).strip() or "Unspecified topic",
            })
    return records


def _recommendations(averages: Dict[str, Optional[float]], topic_scores: Dict[str, float], weak_topics: list[str], weak_categories: list[str]) -> list[str]:
    recommendations = []
    correctness = averages.get("correctness")
    if correctness is not None and correctness < DEFAULT_WEAK_THRESHOLD:
        recommendations.append("Review core technical concepts related to the questions you struggled with.")
    completeness = averages.get("completeness")
    if completeness is not None and completeness < DEFAULT_WEAK_THRESHOLD:
        recommendations.append("Practice giving structured and complete answers.")
    communication = averages.get("communication")
    if communication is not None and communication < DEFAULT_WEAK_THRESHOLD:
        recommendations.append("Practice explaining ideas clearly and concisely.")
    for topic in weak_topics[:3]:
        recommendations.append(f"Spend more time practicing {topic} interview questions.")
    for category in weak_categories[:2]:
        if category not in {"Technical", "HR", "Behavioral"}:
            continue
        recommendations.append(f"Practice more {category.lower()} interview answers.")
    return recommendations or ["Keep practicing to maintain and strengthen your interview performance."]


def calculate_interview_performance(
    answers: Iterable[Dict[str, Any]],
    total_questions: Optional[int] = None,
    strong_threshold: float = DEFAULT_STRONG_THRESHOLD,
    weak_threshold: float = DEFAULT_WEAK_THRESHOLD,
    min_topic_questions: int = DEFAULT_MIN_TOPIC_QUESTIONS,
) -> Dict[str, Any]:
    """Aggregate valid individual answer evaluations into dashboard data.

    Invalid or unevaluated answers are excluded from score averages but remain
    part of answered_questions. Topic labels need multiple evaluated questions
    before they are classified as strong or weak areas.
    """
    answer_list = [answer for answer in answers if isinstance(answer, dict)]
    records = _evaluation_records(answer_list)
    evaluations = [record["evaluation"] for record in records]
    topic_values: dict[str, list[float]] = defaultdict(list)
    category_values: dict[str, list[float]] = defaultdict(list)

    for record in records:
        score = record["evaluation"]["overall_score"]
        topic_values[record["topic"]].append(float(score))
        category = record["category"].title()
        if category in {"Technical", "Hr", "Behavioral"}:
            category = "HR" if category == "Hr" else category
            category_values[category].append(float(score))

    topic_scores = {topic: _average(values) for topic, values in topic_values.items()}
    category_scores = {category: _average(values) for category, values in category_values.items()}
    averages = {
        "relevance": _average(_score_values(evaluations, "relevance")),
        "correctness": _average(
            _score_values(evaluations, "technical_correctness")
            + _score_values(evaluations, "content_quality")
        ),
        "completeness": _average(_score_values(evaluations, "completeness")),
        "communication": _average(_score_values(evaluations, "communication")),
    }
    overall_values = _score_values(evaluations, "overall_score")
    overall_score = _average(overall_values)
    qualified_topics = {
        topic: score
        for topic, score in topic_scores.items()
        if len(topic_values[topic]) >= min_topic_questions and score is not None
    }
    strong_areas = [topic for topic, score in qualified_topics.items() if score >= strong_threshold]
    strong_areas.extend(category for category, score in category_scores.items() if score is not None and score >= strong_threshold)
    weak_topics = [topic for topic, score in qualified_topics.items() if score < weak_threshold]
    weak_categories = [category for category, score in category_scores.items() if score is not None and score < weak_threshold]
    weak_areas = weak_topics + weak_categories

    return {
        "overall_score": overall_score,
        "total_questions": total_questions if total_questions is not None else len(answer_list),
        "answered_questions": len(answer_list),
        "evaluated_questions": len(records),
        "highest_score": max(overall_values) if overall_values else None,
        "lowest_score": min(overall_values) if overall_values else None,
        "averages": averages,
        "category_scores": category_scores,
        "topic_scores": topic_scores,
        "topic_question_counts": {topic: len(values) for topic, values in topic_values.items()},
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "recommendations": _recommendations(averages, topic_scores, weak_topics, weak_categories),
        "thresholds": {
            "strong": strong_threshold,
            "weak": weak_threshold,
            "minimum_topic_questions": min_topic_questions,
        },
    }
