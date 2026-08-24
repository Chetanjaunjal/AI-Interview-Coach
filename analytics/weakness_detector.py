"""Deterministic, user-scoped weak-topic analysis."""

from collections import defaultdict
from typing import Any

from database.db import DatabaseError, get_user_interview_records

WEAK_SCORE_THRESHOLD = 6.0
STRONG_SCORE_THRESHOLD = 8.0
MIN_ATTEMPTS_FOR_CONFIDENT_RESULT = 2
RECENT_INTERVIEWS = 2


def _score(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 10 else None


def _average(values):
    return round(sum(values) / len(values), 1) if values else None


def _trend(previous, recent):
    if previous is None or recent is None:
        return "not_enough_data"
    difference = round(recent - previous, 1)
    if difference >= 0.5:
        return "improving"
    if difference <= -0.5:
        return "declining"
    return "stable"


def _concepts(records):
    counts = defaultdict(int)
    for record in records:
        for concept in record.get("missing_concepts", []):
            normalized = str(concept).strip()
            if normalized:
                counts[normalized] += 1
    return [concept for concept, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))]


def detect_weak_topics(user_id, app=None):
    """Aggregate persisted evaluations for one user into practice recommendations."""
    records = get_user_interview_records(user_id, app)
    topic_records = defaultdict(list)
    category_records = defaultdict(list)
    interview_dates = []
    for record in records:
        score = _score(record.get("overall_score"))
        if score is None:
            continue
        record["missing_concepts"] = record.get("missing_concepts", [])
        topic = str(record.get("topic") or "Unspecified topic").strip()
        category = str(record.get("category") or "Unspecified category").strip()
        topic_records[topic].append(record)
        category_records[category].append(record)
        if record.get("interview_id") not in interview_dates:
            interview_dates.append(record.get("interview_id"))

    def build_area(name, items):
        scores = [_score(item.get("overall_score")) for item in items]
        scores = [score for score in scores if score is not None]
        average = _average(scores)
        ordered = sorted(items, key=lambda item: (item.get("completed_at") or "", item.get("answer_id") or 0), reverse=True)
        recent_ids = set(interview_dates[:RECENT_INTERVIEWS])
        recent = [_score(item.get("overall_score")) for item in ordered if item.get("interview_id") in recent_ids]
        previous = [_score(item.get("overall_score")) for item in ordered if item.get("interview_id") not in recent_ids]
        status = "potential_weakness" if len(scores) < MIN_ATTEMPTS_FOR_CONFIDENT_RESULT and average < WEAK_SCORE_THRESHOLD else "weak" if average < WEAK_SCORE_THRESHOLD else "strong" if average >= STRONG_SCORE_THRESHOLD else "average"
        practice_items = [item for item in items if item.get("interview_type") == "practice"]
        practice_scores = [_score(item.get("overall_score")) for item in practice_items]
        practice_scores = [score for score in practice_scores if score is not None]
        return {"topic": name, "category": name, "questions": len(items), "attempts": len(items), "interviews": len({item.get("interview_id") for item in items}), "practice_attempts": len({item.get("interview_id") for item in practice_items}), "last_practiced": max((item.get("completed_at") for item in practice_items), default=None), "practice_average": _average(practice_scores), "average_score": average, "average_relevance": _average([_score(item.get("relevance_score")) for item in items if _score(item.get("relevance_score")) is not None]), "average_correctness": _average([_score(item.get("correctness_score")) for item in items if _score(item.get("correctness_score")) is not None]), "average_completeness": _average([_score(item.get("completeness_score")) for item in items if _score(item.get("completeness_score")) is not None]), "average_communication": _average([_score(item.get("communication_score")) for item in items if _score(item.get("communication_score")) is not None]), "status": status, "trend": _trend(_average(previous), _average(recent)), "previous_average": _average(previous), "recent_average": _average(recent), "missing_concepts": _concepts(items)}

    areas = [build_area(name, items) for name, items in topic_records.items()]
    categories = [build_area(name, items) for name, items in category_records.items()]
    weak_topics = [area for area in areas if area["status"] in {"weak", "potential_weakness", "average"}]
    strong_topics = [area for area in areas if area["status"] == "strong" and area["attempts"] >= MIN_ATTEMPTS_FOR_CONFIDENT_RESULT]
    weak_categories = [area for area in categories if area["status"] in {"weak", "potential_weakness"} and area["attempts"] >= MIN_ATTEMPTS_FOR_CONFIDENT_RESULT]
    recommendations = []
    for area in sorted(weak_topics, key=lambda item: (item["average_score"] is None, item["average_score"] or 99)):
        concepts = ", ".join(area["missing_concepts"][:3])
        focus = f" focusing on {concepts}" if concepts else ""
        recommendations.append(f"Practice {area['topic']} interview questions{focus}.")
    if any(area["average_communication"] is not None and area["average_communication"] < WEAK_SCORE_THRESHOLD for area in categories):
        recommendations.append("Practice explaining answers using a clear structure: definition, explanation, and example.")
    if any(area["average_completeness"] is not None and area["average_completeness"] < WEAK_SCORE_THRESHOLD for area in categories):
        recommendations.append("Practice giving complete answers and covering all important parts of the question.")
    return {"weak_topics": weak_topics, "strong_topics": strong_topics, "weak_categories": weak_categories, "categories": categories, "recommendations": recommendations, "has_data": bool(records)}
