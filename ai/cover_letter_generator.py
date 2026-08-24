"""Truth-preserving cover-letter generation using the existing AI client."""

import json
import re

TONES = {"professional", "confident", "friendly", "concise"}
LENGTHS = {"short": "150 to 200 words", "medium": "250 to 350 words", "long": "350 to 500 words"}


def validate_options(tone, length):
    if tone not in TONES:
        return "Choose a supported cover-letter tone."
    if length not in LENGTHS:
        return "Choose a supported cover-letter length."
    return None


def build_prompt(resume, job, matching, tone, length, tailored=None):
    source = tailored or resume
    return f"""Write a personalized cover letter using only verified facts from the supplied candidate data. Never invent employers, titles, experience, skills, projects, certifications, achievements, metrics, or technologies. Do not claim a missing job skill. Use relevant existing projects and experience only. Tone: {tone}. Target length: {LENGTHS[length]}. Return JSON with subject, greeting, body (array of paragraphs), closing, name, and personalization_points. Do not include analysis.\nRESUME: {json.dumps(resume, ensure_ascii=True)}\nTAILORED RESUME: {json.dumps(source, ensure_ascii=True)}\nJOB: {json.dumps(job, ensure_ascii=True)}\nMATCHING: {json.dumps(matching, ensure_ascii=True)}"""


def _suspicious(text):
    lowered = text.casefold()
    return bool(re.search(r"\b\d+\s*years?\b|\b\d+[,.]?\d*%\b|\bteam of \d+\b|\[.*?\]|lorem ipsum", lowered))


def validate_output(output, resume, max_body_length=500):
    if not isinstance(output, dict) or not isinstance(output.get("subject"), str) or not isinstance(output.get("greeting"), str) or not isinstance(output.get("body"), list) or not isinstance(output.get("closing"), str) or not isinstance(output.get("name"), str):
        return None, "AI returned invalid cover-letter data."
    body = [item.strip() for item in output["body"] if isinstance(item, str) and item.strip()]
    content = " ".join([output["subject"], output["greeting"], *body, output["closing"], output["name"]])
    if not body or len(content) > max_body_length * 10:
        return None, "The generated cover letter was empty or too long."
    if _suspicious(content):
        return {**output, "body": body}, "Review recommended: this letter may contain an unsupported claim."
    allowed_name = str(resume.get("name", "")).strip()
    if allowed_name and allowed_name != "Not mentioned" and output["name"].strip() != allowed_name:
        return None, "The generated name did not match the resume."
    return {**output, "body": body}, None


def generate_cover_letter(resume, job, matching, tone, length, client, model, tailored=None):
    error = validate_options(tone, length)
    if error:
        return {"success": False, "error": error}
    try:
        response = client.chat.completions.create(model=model, messages=[
            {"role": "system", "content": "You are a factual career-writing assistant. Use only supplied candidate facts. Never invent experience or metrics. Return valid JSON only."},
            {"role": "user", "content": build_prompt(resume, job, matching, tone, length, tailored)},
        ], temperature=0.2, max_tokens=1200)
        parsed = json.loads(response.choices[0].message.content if response.choices else "")
        validated, warning = validate_output(parsed, resume)
        if validated is None:
            return {"success": False, "error": warning or "AI returned invalid cover-letter data."}
        return {"success": True, "cover_letter": validated, "warning": warning}
    except Exception:
        return {"success": False, "error": "Unable to generate the cover letter right now."}
