# Commit #9 Interview Preparation

## Concepts

- **Flask sessions:** Temporary per-browser data stored by Flask in a signed cookie. This prototype uses it for interview questions, index, metadata, and submitted answers.
- **State management:** Keeping track of changing facts. The interview state records which question is current and which answers exist.
- **HTTP requests:** Browser messages to the server. Loading a page uses a request, and submitting an answer sends another request.
- **GET vs POST:** GET reads a page such as `/interview`; POST changes state such as `/start-interview` or `/submit-answer`.
- **Form submission:** The interview form sends a question ID and answer to the backend.
- **Request validation:** The backend checks IDs, answer size, and answer content instead of trusting browser data.
- **Session data:** The server-owned temporary question list, current index, interview metadata, and answer records.
- **Question IDs:** Stable identifiers connect each answer to its exact question and prevent the browser from changing question text.
- **Backend vs frontend state:** The frontend displays the current state; the backend decides which question is current and whether a submission is valid.
- **Progress calculation:** `(current index + 1) / total questions * 100` creates the dynamic progress bar.
- **Error handling:** Invalid requests return a friendly message and leave the interview state unchanged.

## Twenty Interview Questions

1. **Why did you need session management?** The interview spans multiple HTTP requests, so the app needs to remember questions, progress, and answers between requests. **Understand:** HTTP is stateless by default.
2. **How does Flask session work?** Flask signs session data with the app secret and sends it in a browser cookie, which Flask reads on later requests. **Understand:** signing detects tampering but is not encryption.
3. **How do you track the current question?** The session stores `current_index`, and the backend reads the question at that index. **Understand:** the server controls interview order.
4. **How do you store answers?** Each answer record stores `question_id`, question text, answer text, category, and difficulty. **Understand:** records preserve context for later evaluation.
5. **Why use question IDs?** IDs are stable and unambiguous, unlike question text, which may be duplicated or edited. **Understand:** identifiers protect data relationships.
6. **Why use POST for submitting answers?** Submission changes server state, so POST communicates that mutation and avoids using a bookmarkable read request. **Understand:** HTTP methods express intent.
7. **How do you validate answers?** The backend rejects missing, whitespace-only, and over-10,000-character answers. **Understand:** browser validation alone is not security.
8. **How do you prevent duplicate submissions?** The backend accepts only the current question ID and checks whether that ID already has an answer. **Understand:** repeated requests must be idempotent or safely rejected.
9. **What happens if the user refreshes?** A GET reloads the current server session state, so saved answers and position are preserved. **Understand:** refresh does not recreate the interview.
10. **How do you calculate interview progress?** It divides the one-based displayed question number by the total count and converts it to a percentage. **Understand:** progress is derived, not hard-coded.
11. **Why separate backend and frontend state?** The browser is easy to modify, so it should display state while the backend authoritatively validates IDs and order. **Understand:** never trust client-controlled workflow data.
12. **How do you handle invalid question indexes?** Route state validation checks that the index is an integer within the question list; invalid state redirects safely. **Understand:** indexes must be bounded.
13. **How do you handle missing interview sessions?** `/interview`, submission, and summary routes show a friendly message and redirect home or require a new start. **Understand:** missing state is a normal user path.
14. **How do you prevent users from modifying question data?** The form submits only an ID and answer; the backend resolves the question from its signed session copy. **Understand:** never accept client-supplied question text as authority.
15. **Why did you not use a database yet?** This is a temporary, single-browser prototype with no history or multi-user requirement. **Understand:** persistence adds schema, ownership, and lifecycle complexity.
16. **What happens when the interview is completed?** The final answer is saved, active state is removed, and a completed snapshot renders the answer-only summary. **Understand:** completion is a distinct lifecycle state.
17. **How would you persist interview history later?** Store interview metadata, questions, and answer records in database tables linked by an interview ID and user ID. **Understand:** normalized persistent relationships.
18. **How would you support multiple users?** Add authentication, server-side ownership checks, and user-linked interview records. **Understand:** a browser cookie is not a user identity system.
19. **What are Flask session limitations here?** Cookies have size limits, are browser-scoped, and default signed sessions are not encrypted. **Understand:** larger or sensitive production data belongs server-side.
20. **How would you redesign this for production?** Use authenticated server-side storage, expiration, CSRF protection, request limits, observability, and durable interview records. **Understand:** production adds security, scale, and recovery requirements.

## Test Expectations

- Generate 5 and start: `/start-interview` creates state and `/interview` shows Question 1 of 5.
- Submit a valid answer: the answer is linked by ID and Question 2 appears.
- Submit an empty answer: the same question remains active with a validation message.
- Complete all questions: active state ends and the answer-only summary appears without scores or feedback.
- Refresh the interview page: current index and prior answers remain intact.
- Access `/interview` without starting: the user is redirected with a friendly prompt.
- Submit the same answer twice: the second stale request is rejected and no duplicate record is created.
- Start again: index returns to zero and the answer list is emptied.

## Future Features

Later commits can add AI answer evaluation, technical correctness, communication and relevance scoring, personalized feedback, an overall score, learning recommendations, interview history, and voice-based interviews. They are deliberately not implemented here.
