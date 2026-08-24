"""Truth-preserving resume tailoring and deterministic ATS analysis."""

import json
from typing import Any, Optional

from ai.matcher import find_hybrid_matches, normalize_skill

KEYWORD_WEIGHT = 0.35
SKILL_WEIGHT = 0.35
SECTION_WEIGHT = 0.15
RELEVANCE_WEIGHT = 0.15
RESUME_SECTIONS = ("summary", "skills", "experience", "projects", "education", "certifications", "achievements")


def _as_list(value):
    return value if isinstance(value, list) else []


def analyze_resume_keywords(resume_data, job_data):
    """Find job keywords, resume matches, and gaps without inventing candidate skills."""
    resume_skills = [str(item).strip() for item in _as_list(resume_data.get("skills")) if str(item).strip()]
    job_skills = [str(item).strip() for item in _as_list(job_data.get("required_skills")) + _as_list(job_data.get("preferred_skills")) if str(item).strip()]
    matched, missing, semantic = find_hybrid_matches(resume_skills, job_skills)
    matched_names = [item.get("job_skill") for item in matched]
    present_text = " ".join(json.dumps(value, ensure_ascii=True) for value in resume_data.values()).casefold()
    present_keywords = [keyword for keyword in job_skills if normalize_skill(keyword) in present_text]
    missing_keywords = [keyword for keyword in job_skills if keyword not in present_keywords and keyword not in matched_names]
    sections = {section: bool(resume_data.get(section)) and resume_data.get(section) != "Not mentioned" for section in RESUME_SECTIONS}
    return {"required_keywords": job_skills, "present_keywords": sorted(set(present_keywords + matched_names)), "missing_keywords": missing_keywords, "semantic_matches": semantic, "sections": sections}


def calculate_ats_score(keyword_analysis, resume_data, job_data):
    required = [str(item).strip() for item in _as_list(job_data.get("required_skills")) if str(item).strip()]
    present = {normalize_skill(item) for item in keyword_analysis.get("present_keywords", [])}
    keyword_score = (len(present & {normalize_skill(item) for item in required}) / len(required) * 100) if required else 100
    all_job = {normalize_skill(item) for item in keyword_analysis.get("required_keywords", [])}
    skill_score = len(present & all_job) / len(all_job) * 100 if all_job else 100
    section_score = sum(keyword_analysis.get("sections", {}).values()) / len(RESUME_SECTIONS) * 100
    title = str(job_data.get("job_title", "")).casefold()
    resume_text = json.dumps(resume_data, ensure_ascii=True).casefold()
    relevance_score = 100 if title and any(word in resume_text for word in title.split() if len(word) > 3) else 60
    total = round(keyword_score * KEYWORD_WEIGHT + skill_score * SKILL_WEIGHT + section_score * SECTION_WEIGHT + relevance_score * RELEVANCE_WEIGHT)
    return {"score": max(0, min(100, total)), "keyword_match": round(keyword_score), "skills_match": round(skill_score), "section_structure": round(section_score), "role_relevance": round(relevance_score), "estimated": True}


def validate_tailored_output(output, resume_data):
    if not isinstance(output, dict) or not isinstance(output.get("summary"), str):
        return None
    for field in ("skills", "experience", "projects", "certifications", "changes"):
        if not isinstance(output.get(field), list):
            return None
    allowed_skills = {normalize_skill(item) for item in _as_list(resume_data.get("skills"))}
    if any(normalize_skill(item) not in allowed_skills for item in output["skills"] if isinstance(item, str)):
        return None
    return output


def build_tailoring_prompt(resume_data, job_data, keyword_analysis):
    return f"""Tailor this resume truthfully for the target job. Only rewrite or reorder information explicitly present in the original resume. Never add a skill, project, employer, title, certification, achievement, metric, or technology that is absent from the original resume. Missing job skills must remain gaps and may be mentioned only in changes or suggestions, never in claimed skills. Preserve factual names, dates, employers, and project names. Return only JSON with summary, skills, experience, projects, certifications, and changes.\n\nORIGINAL RESUME:\n{json.dumps(resume_data, ensure_ascii=True)}\n\nJOB CONTEXT:\n{json.dumps(job_data, ensure_ascii=True)}\n\nKEYWORD ANALYSIS:\n{json.dumps(keyword_analysis, ensure_ascii=True)}"""


def tailor_resume(resume_data, job_data, keyword_analysis, client=None, model=None):
    if not isinstance(resume_data, dict) or not isinstance(job_data, dict):
        return {"success": False, "error": "Resume and job data are required."}
    if client is None:
        return {"success": False, "error": "AI service is not configured. Please set OPENAI_API_KEY."}
    try:
        response = client.chat.completions.create(model=model, messages=[
            {"role": "system", "content": "You are a truth-preserving resume editor. Never invent candidate facts, skills, experience, projects, certifications, titles, companies, achievements, technologies, or metrics. Return valid JSON only."},
            {"role": "user", "content": build_tailoring_prompt(resume_data, job_data, keyword_analysis)},
        ], temperature=0.2, max_tokens=2200)
        content = response.choices[0].message.content if response.choices else ""
        parsed = json.loads(content)
        validated = validate_tailored_output(parsed, resume_data)
        return {"success": True, "tailored": validated} if validated else {"success": False, "error": "AI returned invalid resume data."}
    except Exception:
        return {"success": False, "error": "Unable to tailor the resume right now. Please try again."}
