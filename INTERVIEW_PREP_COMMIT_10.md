# Commit #10 Interview Preparation

## Concepts

- **LLM evaluation:** Comparing an answer with its question using a model guided by explicit criteria.
- **Evaluation rubric:** A repeatable list of criteria and a 0-10 scale for judging an answer.
- **Structured output:** Required JSON fields for scores and written feedback.
- **Prompt engineering:** Instructions that define fairness, category rules, grounding, and the exact output contract.
- **Hallucination:** An unsupported claim. The evaluator is told to judge only supplied question, answer, and job context.
- **JSON validation:** Checking that the model returned the required fields, types, arrays, and score ranges.
- **Weighted scoring:** Combining criteria with agreed weights rather than treating every criterion as equally important.
- **Deterministic scoring:** Python calculates the final score using fixed weights and decimal half-up rounding.
- **API error handling:** A model failure becomes a safe user message; the saved answer is preserved.
- **Token usage:** Compact current-question context reduces cost, latency, and unnecessary model input.
- **AI limitations:** Model feedback can be useful but remains subjective, approximate, and dependent on upstream question quality.

## Twenty Interview Questions

1. **How does your answer evaluation system work?** It saves the answer, sends the current question and compact context to `answer_evaluator.py`, validates the JSON response, calculates the overall score in Python, and renders feedback.
   **Understand:** The architecture separates Flask workflow from LLM logic.
2. **Why do you use a rubric?** A rubric makes evaluation more consistent, explainable, and testable.
   **Understand:** Scores need defined criteria, not vague model judgment.
3. **What criteria do you evaluate?** Technical answers use relevance, technical correctness, completeness, and communication; HR and behavioral answers use content quality instead of technical correctness.
   **Understand:** Evaluation is category-aware.
4. **Why calculate the final score in Python?** Fixed application logic makes the result reproducible and transparent.
   **Understand:** The model supplies evidence scores; the application owns the formula.
5. **Why not let the LLM directly return the final score?** LLMs can apply weights inconsistently, while Python applies the configured weights every time.
   **Understand:** Separate judgment from deterministic aggregation.
6. **How do you handle technical questions?** The prompt prioritizes correctness and asks the model to identify incorrect claims and missing concepts.
   **Understand:** Technical correctness is a dedicated criterion.
7. **How do you handle HR questions?** They use content quality instead of technical correctness and consider motivation, self-awareness, teamwork, and role relevance.
   **Understand:** A nontechnical answer should not be penalized for lacking technical detail.
8. **How do you handle behavioral questions?** They use content quality, relevance, completeness, and communication; STAR is a helpful lens, not a mandatory format.
   **Understand:** Structure can guide feedback without becoming a rigid rule.
9. **What is structured output?** It is a defined JSON object with known score and feedback fields.
   **Understand:** Predictable data is easier to validate and display.
10. **How do you validate AI-generated scores?** Python requires numeric values from 0 through 10 and rejects booleans, missing fields, and invalid types.
    **Understand:** Model output is untrusted input.
11. **How do you handle hallucination?** The prompt limits the evaluator to supplied facts and asks it to identify answer claims rather than invent candidate history.
    **Understand:** Grounding reduces unsupported feedback.
12. **How do you handle API failures?** The answer is already saved, a safe failure message is shown, and the user can continue.
    **Understand:** Evaluation failure must not destroy user data.
13. **What happens if AI returns invalid JSON?** Parsing or schema validation fails gracefully, with no evaluation attached and no stack trace exposed.
    **Understand:** External responses need defensive parsing.
14. **How do you prevent losing a user’s answer?** The answer record is appended to the session before the evaluator is called.
    **Understand:** Persistence order matters.
15. **How do you control API costs?** Only the current question, answer, category, difficulty, topic, and relevant job fields are sent.
    **Understand:** Smaller context means fewer tokens and lower latency.
16. **Why don’t you send the entire resume every time?** The current answer can be evaluated from local question context and selected job requirements, so the full resume is redundant.
    **Understand:** Relevance filtering improves efficiency.
17. **What are the limitations of AI-based interview evaluation?** Scores are approximate, can vary with wording and model behavior, and cannot objectively measure a person’s ability.
    **Understand:** Feedback should support practice, not make high-stakes decisions alone.
18. **How would you improve evaluation accuracy?** Use expert-labeled examples, calibrated rubrics, domain-specific criteria, and human review for uncertain cases.
    **Understand:** Better evaluation needs evidence and calibration.
19. **How would you test the evaluator?** Test valid excellent, partial, incorrect, short, HR, and behavioral outputs plus malformed JSON, API failure, missing fields, and out-of-range scores.
    **Understand:** Both model contracts and workflow failures need coverage.
20. **How would you make this system production-ready?** Move answers and evaluations to authenticated server-side storage, add CSRF protection, rate limits, timeouts, monitoring, privacy controls, and rubric versioning.
    **Understand:** Production requires security, durability, and auditability.

## Test Expectations

- Excellent technical answer: valid high rubric scores and a Python-calculated high overall score.
- Partially correct answer: model can identify missing concepts and return a moderate score.
- Incorrect technical answer: low technical correctness plus constructive explanation.
- Empty answer: request is rejected before evaluation.
- Very short answer: evaluator can mark completeness low without shaming the user.
- Good HR answer: content quality is used instead of technical correctness.
- Good behavioral answer: relevance, content quality, completeness, and communication are evaluated.
- Invalid JSON: safe invalid-data error and no evaluation card.
- API failure: answer remains saved and the next-question action remains available.
- Out-of-range score: validation rejects the evaluation and does not display an invalid score.

## Future Features

Later commits can add an overall interview score, performance dashboards, weak-topic detection, learning roadmaps, answer history, voice answers, speech-to-text, communication analysis, and interview analytics. They are intentionally not implemented in Commit #10.
