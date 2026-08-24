# Architecture

Flask routes coordinate authenticated workflows. Jinja templates and browser JavaScript provide the UI. SQLite stores users, resumes, jobs, interviews, questions, answers, tailored resumes, and cover letters. The AI layer uses the configured OpenAI client for natural-language analysis, generation, evaluation, tailoring, and explanations. Analytics performs deterministic matching, scoring, weakness detection, roadmap calculations, and readiness.

```text
User -> Authentication -> Dashboard
  -> Resume/Job Analysis -> Matching
  -> Tailoring/Cover Letter or Text/Voice Interview
  -> Evaluation -> Analytics -> Roadmap -> Practice -> Dashboard
```

Voice mode converts an editable browser transcript into the same answer path as typed interviews. Uploaded files are validated and extracted before analysis.
