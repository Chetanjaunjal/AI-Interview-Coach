# Project Audit

## Current Architecture

Flask owns routing and session state. The `ai/` package handles LLM calls and matching. The `analytics/` package calculates interview performance, weaknesses, job plans, and roadmaps. SQLite access is centralized in `database/db.py`. Jinja templates and static JavaScript/CSS provide the browser UI.

## Existing Modules

- Resume PDF upload and extraction
- Resume and job analysis through the existing OpenAI client
- Exact and semantic skill matching
- Text and voice interview sessions
- Answer evaluation and deterministic analytics
- User authentication and scoped history
- Practice mode and job-specific preparation
- Resume tailoring, ATS estimates, and PDF export
- Learning roadmap and daily plan

## Database Tables

`users`, `resumes`, `jobs`, `interviews`, `questions`, `answers`, and `tailored_resumes` exist. Foreign keys and user-scoped queries are used. Interview rows link to users and optional jobs; answers link to questions.

## API Routes

Resume analysis, job analysis, matching, and question generation are JSON APIs. Interview, practice, job, resume, roadmap, and history workflows use authenticated Flask routes.

## AI Features

AI is used for resume analysis, job analysis, question generation, answer evaluation, resume tailoring, and optional roadmap explanations. Python performs matching, averages, thresholds, trends, ATS estimates, and roadmap scoring.

## Security Issues

- No CSRF token protection on state-changing forms.
- AI endpoints have no request rate limiting.
- Development secret fallback is unsafe for production.
- Error handling is inconsistent across routes.
- Upload validation should check MIME/content as well as extension.
- The session stores substantial temporary interview data.

## Performance Issues

- Semantic embeddings may be recomputed during matching.
- Dashboard and roadmap perform multiple database queries per request.
- AI calls can be repeated without a request-level guard.
- No explicit production server or deployment configuration exists.

## Duplicate Code

- Navigation is repeated across templates.
- Similar scoped lookup and friendly-error patterns appear in several routes.
- Existing feature modules are otherwise reasonably separated.

## Potential Bugs

- The active application depends on optional packages that may be missing from the selected interpreter.
- Current development mode is enabled by `app.run(debug=True)`.
- Some legacy compatibility database helpers remain unscoped; web routes use scoped versions.
- The voice browser APIs are inherently unavailable in some browsers.

## Missing Tests

- Full authenticated end-to-end workflow
- Health and error pages
- CSRF behavior
- Rate limiting
- Data export and account deletion
- Upload MIME/content validation
- Dashboard/readiness integration
- Browser-level responsive and voice fallback behavior

## Recommended Improvements

1. Centralize environment configuration and production settings.
2. Add sanitized logging, health checks, and custom 404/403/500 pages.
3. Add lightweight in-process rate limiting for expensive AI routes.
4. Add CSRF protection for state-changing browser requests.
5. Add unified readiness/report routes and dashboard summary data.
6. Add user-scoped JSON export and confirmed account deletion.
7. Add focused integration and security tests.
8. Keep AI failures non-fatal and calculations deterministic.
