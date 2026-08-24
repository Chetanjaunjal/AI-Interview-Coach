"""Deterministic unified interview-readiness scoring."""

INTERVIEW_WEIGHT = 0.30
SKILL_MATCH_WEIGHT = 0.25
PRACTICE_WEIGHT = 0.20
MASTERY_WEIGHT = 0.15
RECENT_PERFORMANCE_WEIGHT = 0.10


def calculate_readiness(performance, roadmap, interviews, active_job=None):
    interview_score = (performance.get("overall_score") or 0) * 10
    roadmap_topics = roadmap.get("topics", []) if isinstance(roadmap, dict) else []
    mastery_score = sum(item["mastery_score"] for item in roadmap_topics) / len(roadmap_topics) if roadmap_topics else interview_score
    practice_scores = [item.get("practice_average") for item in roadmap_topics if item.get("practice_average") is not None]
    practice_score = (sum(practice_scores) / len(practice_scores) * 10) if practice_scores else interview_score
    recent_scores = [item.get("recent_average") for item in roadmap_topics if item.get("recent_average") is not None]
    recent_score = (sum(recent_scores) / len(recent_scores) * 10) if recent_scores else interview_score
    matching = active_job.get("matching_data", {}) if active_job else {}
    required = matching.get("matched_required_skills", []) + matching.get("missing_required_skills", [])
    skill_match = len(matching.get("matched_required_skills", [])) / len(required) * 100 if required else 0
    score = round(interview_score * INTERVIEW_WEIGHT + skill_match * SKILL_MATCH_WEIGHT + practice_score * PRACTICE_WEIGHT + mastery_score * MASTERY_WEIGHT + recent_score * RECENT_PERFORMANCE_WEIGHT)
    return {"overall": max(0, min(100, score)), "interview": round(interview_score), "job_match": round(skill_match), "practice": round(practice_score), "mastery": round(mastery_score), "recent": round(recent_score), "job": active_job, "interviews": interviews}
