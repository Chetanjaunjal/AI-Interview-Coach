# Commit #8 Interview Preparation

## Concepts

- **LLM:** A large language model predicts useful text from patterns learned from large amounts of data. Here it turns structured candidate and job context into interview questions.
- **Prompt engineering:** Writing clear instructions, constraints, and output requirements for the LLM.
- **Context:** The relevant facts supplied to one request: candidate skills, projects, experience, job requirements, and match gaps.
- **Structured output:** A response with predictable fields instead of free-form prose. Each question has `question`, `category`, `difficulty`, `topic`, and `reason`.
- **JSON:** A text format for objects and arrays that both the API and browser can parse.
- **Temperature:** A randomness setting. The generator uses a low value for consistent questions while allowing modest variety.
- **Hallucination:** An unsupported claim generated as if it were true. The system instructs the model to use only supplied candidate facts and treats missing skills as knowledge-check topics.
- **AI personalization:** Connecting a question to this candidate's actual project, skills, experience, or target role.
- **Token usage:** The amount of text processed by the model. Sending compact structured analyses instead of raw documents lowers cost and response time.
- **API error handling:** Catching service/network failures and returning a user-safe message rather than exposing internals or crashing Flask.
- **Input validation:** Restricting interview type, difficulty, and count to known values before making an API request.

## Twenty Interview Questions and Short Answers

1. **How does your question generator work?** It validates the setup, builds a compact context prompt, calls the configured LLM, parses JSON, and validates every question.
2. **How do you personalize questions?** It uses the candidate's real skills, projects, experience, and the target job's requirements and responsibilities.
3. **What information do you provide to the LLM?** Candidate profile fields, job requirements, matched and missing skills, interview type, difficulty, and requested count.
4. **Why use structured JSON?** It makes the response predictable, machine-validated, and easy to render as cards.
5. **Why separate question generation from Flask?** The AI module owns prompts and API behavior, while Flask owns HTTP and session flow; both become easier to test.
6. **How do you prevent duplicate questions?** The validator normalizes question text and rejects repeated values.
7. **How do you control difficulty?** The selected value is validated, explained in the prompt, and required to match every returned question.
8. **How do you control interview type?** The backend accepts only four allow-listed values and gives the model category-specific instructions.
9. **How do you prevent hallucinated candidate information?** The system instruction says to use supplied facts only, and missing skills are framed as questions rather than claimed experience.
10. **How do you handle invalid AI responses?** JSON parsing and field, type, category, difficulty, count, and duplicate checks return a safe error.
11. **What is prompt engineering?** Designing instructions and context to guide the model toward relevant, constrained output.
12. **What is context?** The information the model can use for the current request.
13. **What are tokens?** Small pieces of text used to measure model input and output, which influence cost and limits.
14. **How do you reduce API costs?** Reuse structured analyses and match data instead of sending the entire resume and job text again.
15. **What is temperature?** A parameter that controls output variation; lower values are more consistent.
16. **What is hallucination?** A plausible-sounding but unsupported model claim.
17. **Why generate project-specific questions?** They test work the candidate can actually discuss and make practice more realistic.
18. **How would you improve question quality?** Add stronger category balancing, rubric-based review, and user feedback while keeping facts grounded.
19. **What are limitations of LLM-generated questions?** They can still be repetitive, miss domain nuance, or misunderstand imperfect upstream analysis.
20. **How would you evaluate whether questions are good?** Check relevance, factual grounding, type and difficulty alignment, coverage, uniqueness, and feedback from candidates or interviewers.

## Test Matrix

- Technical + Easy + 5: returns five valid fundamental or technology questions.
- Technical + Hard + 10: returns ten valid deep technical questions.
- HR + Medium + 5: returns five medium HR-focused questions.
- Behavioral + Medium + 5: returns five scenario-based questions.
- Mixed + Hard + 15: returns fifteen valid questions across relevant categories.
- Invalid interview type: returns a validation error without an API call.
- Invalid difficulty: returns a validation error without an API call.
- Invalid question count: rejects values outside 5, 10, and 15.
- Missing resume analysis: asks the user to analyze the resume first.
- Missing job analysis: asks the user to analyze the job description first.
- Malformed JSON: returns an invalid-data error and shows no question cards.

## Future Commits

Future work can add answer input, AI answer evaluation, technical correctness and communication scoring, feedback, an overall interview score, and a personalized learning roadmap. These are intentionally not part of Commit #8.
