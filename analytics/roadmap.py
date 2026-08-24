"""Deterministic personalized learning-roadmap calculations."""

PERFORMANCE_WEIGHT = 0.50
PRACTICE_WEIGHT = 0.20
RECENT_WEIGHT = 0.20
CONSISTENCY_WEIGHT = 0.10


def _status(score):
    if score < 50:
        return "Needs Significant Improvement"
    if score < 70:
        return "Needs Improvement"
    if score < 85:
        return "Good"
    return "Strong"


def _job_relevance(topic, job):
    if not job:
        return 50
    matching = job.get("matching_data", {})
    required = matching.get("missing_required_skills", []) + [item.get("job_skill", "") for item in matching.get("matched_required_skills", []) if isinstance(item, dict)]
    return 100 if any(str(item).casefold() == topic.casefold() for item in required) else 35


def build_roadmap(weakness, jobs=None, active_job=None):
    jobs = jobs or []
    areas = weakness.get("weak_topics", []) + weakness.get("strong_topics", [])
    topics = []
    for area in areas:
        score = area.get("average_score")
        if score is None:
            continue
        performance = score * 10
        practice = (area.get("practice_average") if area.get("practice_average") is not None else score) * 10
        recent = (area.get("recent_average") if area.get("recent_average") is not None else score) * 10
        consistency = max(0, 100 - abs(recent - performance))
        mastery = round(performance * PERFORMANCE_WEIGHT + practice * PRACTICE_WEIGHT + recent * RECENT_WEIGHT + consistency * CONSISTENCY_WEIGHT)
        relevance = _job_relevance(area["topic"], active_job)
        weakness_factor = 100 - mastery
        frequency = min(100, area.get("questions", 0) * 10)
        priority = round(weakness_factor * 0.45 + relevance * 0.30 + frequency * 0.15 + (100 - recent) * 0.10)
        topics.append({**area, "mastery_score": mastery, "priority_score": priority, "status": _status(mastery), "job_relevance": relevance})
    topics.sort(key=lambda item: (-item["priority_score"], item["topic"].casefold()))
    for index, topic in enumerate(topics, 1):
        topic["priority"] = index
        topic["recommended_difficulty"] = "easy" if topic["mastery_score"] < 50 else "medium" if topic["mastery_score"] < 85 else "hard"
    phases = [
        {"name": "Phase 1 - Fix Weak Fundamentals", "topics": [item["topic"] for item in topics if item["mastery_score"] < 70], "goal": "Improve basic correctness."},
        {"name": "Phase 2 - Strengthen Job Skills", "topics": [item["topic"] for item in topics if item["job_relevance"] >= 100 and item["mastery_score"] >= 50], "goal": "Improve job-specific readiness."},
        {"name": "Phase 3 - Interview Practice", "topics": ["Mixed technical and behavioral questions"] if topics and max(item["mastery_score"] for item in topics) >= 70 else [], "goal": "Apply knowledge under interview conditions."},
        {"name": "Phase 4 - Advanced Practice", "topics": ["Hard questions and scenario practice"] if topics and min(item["mastery_score"] for item in topics) >= 70 else [], "goal": "Prepare for difficult interviews."},
    ]
    return {"topics": topics, "phases": phases, "has_data": bool(topics), "job": active_job, "job_readiness": calculate_job_readiness(topics, active_job)}


def calculate_job_readiness(topics, job):
    if not job or not topics:
        return None
    matching = job.get("matching_data", {})
    required = matching.get("matched_required_skills", []) + matching.get("missing_required_skills", [])
    match_score = len(matching.get("matched_required_skills", [])) / len(required) * 100 if required else 0
    performance = sum(item["mastery_score"] for item in topics) / len(topics)
    return round(match_score * 0.4 + performance * 0.6)


def build_daily_plan(roadmap, minutes):
    minutes = minutes if minutes in {30, 60, 90} else 30
    topic = roadmap.get("topics", [{}])[0].get("topic", "interview fundamentals")
    if minutes == 30:
        tasks = [(10, f"Review {topic} concepts"), (15, f"Practice three {topic} questions"), (5, "Answer one interview question")]
    elif minutes == 60:
        tasks = [(20, f"Review {topic} concepts"), (25, f"Practice {topic} questions"), (15, "Answer interview questions")]
    else:
        tasks = [(30, f"Review {topic} concepts"), (35, f"Practice {topic} questions"), (25, "Complete a focused interview")]
    return {"minutes": minutes, "topic": topic, "tasks": tasks}
