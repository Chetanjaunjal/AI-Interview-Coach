"""Deterministic planning for job-specific interview preparation."""


def build_job_interview_plan(job_data, matching, weakness_analysis, difficulty, question_count):
    required = job_data.get("required_skills", []) if isinstance(job_data, dict) else []
    preferred = job_data.get("preferred_skills", []) if isinstance(job_data, dict) else []
    missing = list(matching.get("missing_required_skills", [])) + list(matching.get("missing_preferred_skills", []))
    matched = [item.get("job_skill") or item.get("candidate_skill") for item in matching.get("matched_required_skills", []) if isinstance(item, dict)]
    weak_topics = weakness_analysis.get("weak_topics", []) if isinstance(weakness_analysis, dict) else []
    focus_areas = []
    for item in matched + list(required) + list(preferred) + [item.get("topic") for item in weak_topics]:
        value = str(item or "").strip()
        if value and value.casefold() not in {existing.casefold() for existing in focus_areas}:
            focus_areas.append(value)
    base = question_count // 4
    distribution = {"technical": base, "project": base, "behavioral": base, "hr": question_count - base * 3}
    if question_count < 4:
        distribution = {"technical": question_count, "project": 0, "behavioral": 0, "hr": 0}
    return {
        "role": job_data.get("job_title", "Target role"),
        "difficulty": difficulty.title(),
        "questions": question_count,
        "focus_areas": focus_areas[:8],
        "weak_areas": [item.get("topic") for item in weak_topics[:5]],
        "missing_skills": missing[:8],
        "question_distribution": distribution,
        "has_previous_performance": bool(weakness_analysis.get("has_data")) if isinstance(weakness_analysis, dict) else False,
    }
