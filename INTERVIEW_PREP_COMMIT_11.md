# Commit #11 Interview Preparation

## Concepts

- **Data aggregation:** Combining individual answer evaluations into summaries such as averages and category scores.
- **Average:** Adding valid values and dividing by their count.
- **Weighted average:** An average where some values have more influence. Commit #11 uses a simple average because each completed question contributes one score.
- **KPI:** A key performance indicator, such as overall score, evaluated-question count, highest score, or communication average.
- **Analytics:** Turning stored data into useful findings about performance.
- **Data visualization:** Showing metrics with readable score cards and horizontal bars.
- **Dashboard design:** Choosing a small set of useful summaries so users can act on them quickly.
- **Score normalization:** Keeping scores on the same 0-10 scale before comparing them.
- **Thresholds:** Configurable boundaries that define strong and weak performance. Defaults are 8.0 and 6.0.
- **Deterministic recommendations:** Rules that turn observed low metrics or weak topics into repeatable advice without another LLM call.
- **Backend analytics:** Keeping aggregation in Python rather than trusting browser calculations.
- **Session-based data:** Temporary completed-interview data stored in Flask's session; it can disappear when the session expires or is replaced.

## Twenty Interview Questions

1. **How does your performance dashboard work?** It reads the completed interview session, aggregates valid evaluations with `interview_analytics.py`, and renders the resulting metrics and recommendations.
   **Understand:** The dashboard summarizes existing data and makes no LLM call.
2. **How do you calculate the overall score?** It averages the valid per-question `overall_score` values and rounds to one decimal place.
   **Understand:** Each question has equal weight in the first version.
3. **Why use Python instead of an LLM for calculations?** Python is faster, cheaper, reproducible, and exact for arithmetic.
   **Understand:** Basic statistics do not need generative AI.
4. **How do you calculate category performance?** Evaluated question scores are grouped by normalized category, then averaged independently.
   **Understand:** Technical, HR, and Behavioral results are not mixed together for category metrics.
5. **How do you calculate topic performance?** Scores are grouped by each saved question topic and averaged.
   **Understand:** Persisting the topic with the answer preserves the analytics relationship.
6. **How do you identify strong areas?** Topics with enough evaluated questions and scores at or above the strong threshold are listed, along with strong categories.
   **Understand:** The threshold is a policy setting, not a hidden magic number.
7. **How do you identify weak areas?** Qualified topics and categories below the weak threshold are listed as needs improvement.
   **Understand:** Weaknesses come from measured scores.
8. **Why use configurable thresholds?** Different products or teams may define strong and weak differently, so one constant should not be scattered through the code.
   **Understand:** Configuration makes behavior explainable and adjustable.
9. **How do you handle missing evaluation data?** The answer remains counted as answered, but it is excluded from score aggregates and the dashboard explains when no evaluated answers exist.
   **Understand:** Missing data should not become a fake zero.
10. **How do you handle HR questions without technical scores?** The analytics module uses `content_quality` as the correctness-equivalent metric.
    **Understand:** Different categories have different rubrics but a shared dashboard shape.
11. **What is data aggregation?** Reducing many records into meaningful summaries.
    **Understand:** Individual feedback and aggregate performance answer different questions.
12. **What is a KPI?** A key number that indicates performance, such as overall score or communication average.
    **Understand:** KPIs should support a decision or action.
13. **Why should dashboards be simple?** Too many metrics make important signals harder to notice and act on.
    **Understand:** Clarity is more valuable than decorative complexity.
14. **How do you prevent misleading analytics?** Validate score ranges, ignore malformed evaluations, distinguish answered from evaluated counts, and avoid classifying single-question topics.
    **Understand:** Honest caveats are part of the feature.
15. **What happens if there is only one question about a topic?** Its score is displayed with a single-question note but it is not labeled strong or weak by default.
    **Understand:** Small samples have limited evidence.
16. **Why did you not use a database yet?** The prototype has one temporary completed interview and no history requirement.
    **Understand:** A database becomes necessary for durable history and multiple users.
17. **What happens when the session expires?** The completed interview and dashboard data may be lost.
    **Understand:** Cookie-backed session storage is temporary and browser-scoped.
18. **How would you store interview history in production?** Use authenticated server-side interview, answer, evaluation, and metric records linked to a user and interview ID.
    **Understand:** Durable analytics need ownership and persistence.
19. **How would you improve the analytics system?** Add trends, confidence/sample sizes, configurable category weights, rubric versions, and comparisons across interviews.
    **Understand:** New metrics should be grounded in reliable data.
20. **How would you make the dashboard useful for recruiters or candidates?** Give candidates actionable practice areas while providing recruiters only appropriate, consented summaries with clear limitations.
    **Understand:** Audience and privacy should shape dashboard design.

## Test Expectations

- Perfect interview: all valid scores aggregate to 10.0.
- Mixed performance: 9, 8, 6, and 5 aggregate to 7.0.
- Technical-only interview: only Technical appears in category scores.
- Three categories: each category receives its own average.
- Missing correctness: HR uses content quality without crashing.
- Missing evaluation: answered count remains accurate while evaluated count and score averages exclude it.
- Invalid score: malformed score is ignored safely rather than treated as zero.
- Single topic: topic score displays, but the topic is not classified as strong or weak.
- Very low performance: weak areas and deterministic recommendations appear.
- No completed interview: dashboard redirects with a clear completion message.

## Future Features

Future commits can add persistent interview history, user accounts, multi-interview trends, progress tracking, a learning roadmap, weak-topic practice, interview comparison, advanced analytics, and a recruiter dashboard. They are intentionally not implemented in Commit #11.
