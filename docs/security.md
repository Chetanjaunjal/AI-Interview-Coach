# Security

Authentication uses Werkzeug password hashes and minimal Flask sessions. Private queries filter by the current user ID. SQL uses parameters. Uploads use secure filenames, extension checks, size limits, and PDF extraction. User-generated and AI text is rendered as text, not trusted HTML.

Secrets belong in environment variables. Raw audio is not stored. AI endpoints are rate limited. Error responses are sanitized and logs do not include passwords, API keys, full resumes, or full answers. Production should add CSRF middleware for all browser state-changing forms and HTTPS-secure cookie settings.
