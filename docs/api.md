# API and Routes

Public: `/`, `/register`, `/login`, `/health`.

Authenticated workflows: resume upload/analysis, job analysis/matching, question generation, `/interview`, `/voice-interview`, `/practice`, `/job-prep`, `/resume-tailor`, `/cover-letter`, `/roadmap`, `/readiness`, `/history`, `/profile`, and `/export-data`.

All private resource routes validate the authenticated user before loading or modifying records. Expensive AI routes use the shared rate limiter and return sanitized error messages.
