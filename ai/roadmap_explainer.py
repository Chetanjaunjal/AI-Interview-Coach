"""Optional natural-language explanation for deterministic roadmap results."""

import json


def explain_roadmap(roadmap, client, model):
    if not client or not isinstance(roadmap, dict):
        return None
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Explain an interview learning roadmap in two concise sentences. Use only the supplied facts. Do not change or recalculate scores."},
                {"role": "user", "content": json.dumps({"topics": roadmap.get("topics", [])[:3], "job": roadmap.get("job", {}).get("title") if roadmap.get("job") else None}, ensure_ascii=True)},
            ],
            temperature=0.2,
            max_tokens=180,
        )
        text = response.choices[0].message.content.strip() if response.choices else ""
        return text or None
    except Exception:
        return None
