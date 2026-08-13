# Interview Prep: Resume-Job Matching System (Commit #6)

## Concepts to Study Before Your Interview

### Foundational Concepts

1. **Skill Matching**
   - Comparing two sets of data for similarities
   - Set operations: intersection, difference, union
   - Applications beyond hiring (product compatibility, resource allocation)

2. **Normalization**
   - Standardizing data for consistent comparison
   - Case normalization, whitespace handling
   - Why "Java" and "JAVA" should be equivalent
   - Why "Java" and "JavaScript" must NOT be equivalent

3. **Set Operations in Python**
   - Set data structures and performance
   - Membership testing: O(1) vs O(n)
   - Creating sets from lists
   - Finding intersection and difference

4. **Weighted Scoring**
   - Combining multiple factors with different importance levels
   - Why some factors matter more than others
   - Real-world examples (GPA weighted with test scores)
   - Designing fair scoring systems

5. **Deterministic Algorithms**
   - Same input → same output always
   - Advantages over randomized/AI-based approaches
   - Reproducibility and debugging
   - When to use vs when to avoid

6. **Required vs Preferred Skills**
   - Deal-breakers vs nice-to-haves
   - Business logic: must-haves vs aspirational
   - How hiring actually works
   - Why this distinction matters in scoring

7. **Edge Cases and Data Validation**
   - Empty lists/datasets
   - Missing categories (no preferred skills)
   - Malformed data
   - Graceful degradation

8. **Explainable AI vs Black-Box AI**
   - When to use deterministic logic vs LLM
   - Cost/speed/explainability tradeoffs
   - Debugging: can you explain every decision?
   - User trust and transparency

9. **Separation of Concerns**
   - Why matching logic lives in `matcher.py`, not `app.py`
   - Single responsibility principle
   - Testability and reusability
   - Module independence

10. **Data Structures and Algorithms**
    - Choosing the right data structure (list vs set vs dict)
    - Time complexity analysis
    - Memory efficiency
    - Real-world performance impact

---

## 15 Interview Questions (With Answers and Learning Goals)

### Question 1: How does your resume-job matching system work?

**What to Say:**
"The matching system compares a candidate's resume skills with job requirements to calculate a match percentage. It works in four steps:

1. **Extraction**: We pull skills from two AI-analyzed documents - the resume and the job description
2. **Normalization**: All skills are converted to lowercase and whitespace is trimmed to ensure "Java" and "JAVA" both match
3. **Comparison**: We use exact string matching to identify which candidate skills appear in the job requirements
4. **Scoring**: We use a weighted formula where required skills count 70% and preferred skills count 30%

The result is a match percentage (0-100%) plus detailed breakdowns of matched, missing, and additional skills with personalized recommendations."

**What You Should Understand:**
- The four distinct phases of matching
- Why each phase is necessary
- How the system produces transparent, explainable results
- That this is deterministic (no randomness or LLM calls during matching)

**Follow-up Topics:**
- Why we normalize skills
- Why the weights are 70/30
- What happens with edge cases (no required skills, no preferred skills)

---

### Question 2: How do you calculate the match percentage?

**What to Say:**
"We use a weighted scoring formula that respects the importance of different skill categories:

```
Required Score = Matched Required Skills / Total Required Skills
Preferred Score = Matched Preferred Skills / Total Preferred Skills

Overall Match % = (Required Score × 0.70) + (Preferred Score × 0.30)
```

For example:
- If you have 2/3 required skills and 0/2 preferred: (67% × 0.70) + (0% × 0.30) = ~47%
- If you have 3/3 required skills and 1/2 preferred: (100% × 0.70) + (50% × 0.30) = 85%

We also handle edge cases: if a job has no preferred skills, we only score on required skills. If a job has no required skills, we only score on preferred skills."

**What You Should Understand:**
- The mathematical formula and why it works
- Why 70/30 weighting makes sense
- How edge cases are handled
- That the score is transparent and explainable

**Follow-up Topics:**
- Alternative scoring methods
- Why not equal weighting?
- Why not use geometric mean?
- How would you change the weights?

---

### Question 3: Why did you use a weighted score of 70% for required and 30% for preferred?

**What to Say:**
"The weights reflect hiring reality. In recruitment:

- **Required skills** are deal-breakers. Without them, you typically can't perform the job.
- **Preferred skills** are bonuses. A candidate without them can learn on the job or pick up transferable skills.

Mathematically, this means:
- A candidate with ALL required skills + ZERO preferred = 70% (likely to hire)
- A candidate with ZERO required skills + ALL preferred = 30% (unlikely to hire)

We chose 70/30 because it's a reasonable assumption that required skills are roughly 2-3x more important than preferred skills in most technical roles. However, this is a design choice that could be adjusted for different industries or role types.

The key insight is: **make the weighting transparent so stakeholders can understand and challenge it.**"

**What You Should Understand:**
- Why weighting exists at all
- That 70/30 is a design choice, not a law
- How weighting affects outcomes
- That different roles might need different weights

**Follow-up Topics:**
- How would weights change for different roles? (e.g., internship vs senior engineer)
- How could you make weights configurable?
- What's the impact of changing weights?
- How would you justify weights in a business context?

---

### Question 4: Why are required skills more important than preferred skills?

**What to Say:**
"Required skills are more important because they directly impact job performance:

- A **required skill** (like 'Java' for a Java developer role) is something you need to perform day-to-day tasks
- A **preferred skill** (like 'AWS' or 'Docker') is nice to have but not essential - you can learn it on the job

From a hiring perspective:
- Someone with 'Java' + no 'Docker' can start working immediately and learn Docker
- Someone with 'Docker' but no 'Java' cannot perform the core job

This is why we weight required skills 70% - they're foundational. Preferred skills are 30% because they differentiate candidates when multiple people have the required skills.

In the scoring formula, this means: 'Fulfill the core requirements first, then look at extras.'"

**What You Should Understand:**
- The business logic behind the distinction
- How this applies to real hiring decisions
- Why this impacts scoring
- That this reflects real-world job requirements

**Follow-up Topics:**
- Are there roles where this reverses?
- What if a 'preferred' skill is actually critical?
- How do you decide what's required vs preferred?

---

### Question 5: What is skill normalization and why does it matter?

**What to Say:**
"Skill normalization means converting skills to a standard form so comparisons work correctly. We normalize by:

1. Converting to lowercase: 'Java', 'JAVA', 'java' all become 'java'
2. Trimming whitespace: '  Python  ' becomes 'python'

Why this matters:

**Without normalization:**
- Resume says: 'Java' (proper case)
- Job says: 'java' (lowercase)
- Result: No match ❌ (even though it's the same skill!)

**With normalization:**
- Resume says: 'Java' → normalize → 'java'
- Job says: 'java' → normalize → 'java'
- Result: Match! ✅

Real-world case: An AI resume analyzer might output 'Python', while an auto-generated job posting outputs 'python' from XML tags. Without normalization, we'd miss this match.

We deliberately DON'T do aggressive normalization (stemming, lemmatization) because 'Java' and 'JavaScript' would both become 'java' → false match!"

**What You Should Understand:**
- What normalization is and why it's necessary
- The specific normalizations we do (lowercase, trim whitespace)
- Why we DON'T do stemming/lemmatization
- The tradeoff between catching real matches and avoiding false matches

**Follow-up Topics:**
- What other normalizations could we do?
- Why is stemming dangerous?
- How would you handle abbreviations like 'SQL' vs 'Structured Query Language'?

---

### Question 6: How do you handle "Java" and "JAVA" so they match, but ensure "Java" and "JavaScript" don't match?

**What to Say:**
"Great question! This shows the importance of correct normalization.

**Handling Java vs JAVA (should match):**
```python
def normalize_skill(skill):
    return skill.strip().lower()

normalize_skill('Java')        # → 'java'
normalize_skill('JAVA')        # → 'java'
# These are identical → match! ✅
```

**Distinguishing Java vs JavaScript (must NOT match):**
```python
normalize_skill('Java')        # → 'java'
normalize_skill('JavaScript')  # → 'javascript'
# These are different strings → no match ✅
```

The key is **exact string matching on normalized skills**. We don't try to be 'smart' about semantics. If it's different text, it's a different skill.

This conservative approach prevents false positives:
- React ≠ React Native
- MySQL ≠ MongoDB
- Python ≠ Ruby

Any semantic matching (understanding that Java and JavaScript are both languages) would be a future enhancement using embeddings or an ontology."

**What You Should Understand:**
- How normalization works precisely
- Why exact matching is conservative but safe
- What false positives/negatives are
- That semantic matching is more advanced and requires additional tools

**Follow-up Topics:**
- What if someone writes "javascript" in resume and "JavaScript" in job posting? (Should match - does it?)
- How would you handle abbreviations?
- Could you build a mapping of equivalent skills?

---

### Question 7: Why did you use Python logic instead of another LLM call for matching?

**What to Say:**
"Excellent question about architecture decisions. I chose deterministic Python logic for several reasons:

| Factor | Python Logic | LLM Call |
|--------|------------|----------|
| **Speed** | Instant | 1-2 seconds per request |
| **Cost** | ~$0 | 0.001-0.01 per request |
| **Reproducibility** | Always same result | Might vary (temperature settings) |
| **Explainability** | Can trace every decision | 'Black box' reasoning |
| **Reliability** | Deterministic | Subject to API changes |

**The matching logic is simple:**
- Compare sets of strings
- Apply a formula
- Return results

This doesn't need LLM intelligence. A Python algorithm is:
- 100x faster
- 100x cheaper
- Fully debuggable and explainable

**When we DO use LLM:**
- Resume analysis (requires natural language understanding)
- Job analysis (requires extracting meaning from text)

**When we DON'T:**
- Comparing structured data (matching is pure logic)

This follows the principle: use the right tool for the job."

**What You Should Understand:**
- The tradeoff between AI sophistication and practical efficiency
- When to use AI and when not to
- That simpler solutions are often better
- Cost and performance considerations

**Follow-up Topics:**
- When would using LLM for matching make sense?
- How would an LLM approach look different?
- What are the downsides of asking an LLM to score?

---

### Question 8: What are the advantages of deterministic matching over using an LLM to generate a score?

**What to Say:**
"Deterministic matching has clear advantages over asking an LLM like ChatGPT to 'score the match':

**1. Speed** - Instant (milliseconds) vs waiting for API (1-2 seconds)

**2. Cost** - Free vs ~$0.01 per request
   - For 1000 matches: $10 with LLM, $0 with Python

**3. Reproducibility** - Same result every time
   - LLM might say 65% today and 68% tomorrow due to randomness
   - Users expect consistent results

**4. Explainability** - I can show exactly why
   - User: 'Why is my match 65%?'
   - Me: 'You have 2/3 required skills (67%) and 1/2 preferred (50%). (67% × 0.70) + (50% × 0.30) = 64%'
   - LLM would just say: 'Based on my analysis...' (no clear reasoning)

**5. Auditability** - Developers and auditors can understand and verify it
   - Compliance and trust matter
   - 'I used an LLM' doesn't explain decisions

**6. Reliability** - No API failures or rate limits
   - Python runs locally without dependencies

**Example of the difference:**
```
Python logic: 'Java' found in both → match → always 100% certain
LLM approach: 'Based on semantic similarity, Java is 92% similar...' → varies
```

The LLM approach is overkill for structured data comparison. We save it for the actual hard work: analyzing messy text."

**What You Should Understand:**
- Real advantages (cost, speed, reliability) vs hypothetical ones
- When sophisticated solutions are actually needed
- Engineering thinking about tradeoffs
- That simpler is better unless you have a good reason

**Follow-up Topics:**
- Describe a scenario where LLM matching would be better
- How would you benchmark Python vs LLM?
- What if requirements changed?

---

### Question 9: What are the advantages of having deterministic, explainable matching?

**What to Say:**
"Deterministic, explainable matching has major benefits:

**1. User Trust**
- Users understand why they got a 65% match
- They can verify and challenge the logic
- Transparency builds confidence more than 'trust me' black boxes

**2. Debugging and Improvement**
- If matching seems wrong, I can trace exactly why
- 'Candidate has 'Docker', job has 'docker' - should match'
- Then I can fix the issue with certainty

**3. Legal/Compliance**
- Hiring decisions need to be defensible
- 'The algorithm gave them 65%' is better than 'an AI felt it was 65%'
- Anti-discrimination auditing is possible

**4. Consistency**
- Two identical resume-job pairs always get the same score
- No surprises, no randomness

**5. Performance Metrics**
- I can measure: 'In 100 test cases, the algorithm correctly identified...'
- LLM: 'It got it right most of the time?'

**Example:**
```
User asks: 'Why don't I match for this Java role?'
I can show:
- Resume: [Java, Python, SQL]
- Job Required: [Java, C++, Spring Boot]
- Matched: [Java] = 1/3 = 33%
- Missing: [C++, Spring Boot]

User can immediately see: 'Oh, I need C++ and Spring Boot!'
```

With an LLM, it might just say: 'You seem like a partial fit' (unhelpful)."

**What You Should Understand:**
- Why explainability matters beyond technical reasons
- Business and legal value of transparency
- How this approach enables debugging and improvement
- That users appreciate understanding why they got results

**Follow-up Topics:**
- How would you handle a case where the formula seems unfair?
- Can users adjust weights?
- Should transparency apply to all algorithms?

---

### Question 10: What are the limitations of keyword/skill matching?

**What to Say:**
"Keyword matching has real limitations that we're aware of:

**1. No Semantic Understanding**
- 'REST API' and 'Web API' are the same concept, but don't match
- 'Database' could mean MySQL, PostgreSQL, MongoDB (different technologies)
- 'Machine Learning' and 'ML' won't match without a mapping

**2. No Skill Levels**
- '1 year of Java' matches same as '10 years of Java'
- System can't distinguish junior vs expert
- For some jobs, level is critical

**3. No Dependencies**
- 'Java' doesn't imply 'Object-Oriented Programming'
- 'TypeScript' should imply 'JavaScript' knowledge but doesn't show
- Some skills build on others

**4. No Context**
- 'Database' on resume: Did you design schemas? Just use SQL?
- System can't understand depth or application of skills

**5. No Synonyms**
- 'ML Engineer' vs 'Machine Learning Engineer' are different text
- 'React.js' vs 'React' might be treated as different
- Requires manual mapping or NLP

**Example:**
```
Candidate: 'Python, Pandas, NumPy, scikit-learn'
Job wants: 'Machine Learning'

Keyword match: 0% (no exact match)
Reality: Candidate is highly qualified (ML experience!)
```

**How we address this (future improvements):**
- Use embeddings to find semantic similarity
- Build a skill ontology/graph
- Add level/duration information
- Extract context from descriptions"

**What You Should Understand:**
- The concrete limitations of keyword matching
- That our system is intentionally simple (by design)
- That better solutions exist but are more complex
- Why we're honest about limitations

**Follow-up Topics:**
- How would embeddings help?
- What's a skill ontology?
- Would you ever implement these for Commit #7?

---

### Question 11: What happens when there are no preferred skills in the job?

**What to Say:**
"This is an important edge case. Here's how we handle it:

**Scenario:** Job listing only specifies required skills, no preferred skills

```
Resume: [Java, SQL, Docker, AWS]
Job Required: [Java, SQL]
Job Preferred: [] (empty)

Match calculation:
- Required Score = 2/2 = 100%
- Preferred Score = N/A (no preferred skills)

Result: Only required score matters = 100%
(NOT (100% × 0.70) + (0% × 0.30) = 70%)
```

**Why this is important:**
- If we treated 'no preferred skills' as '0% match', we'd unfairly penalize candidates
- If we treated it as '100% match', we'd give false credit
- We handle it by only evaluating dimensions that have content

**Our logic:**
```python
if total_required > 0 and total_preferred > 0:
    score = (req_score * 0.70) + (pref_score * 0.30)  # Both exist
elif total_required > 0:
    score = req_score  # Only required
else:
    score = pref_score  # Only preferred
```

**Real example:**
- Many job postings focus on required skills and don't list preferred
- Our system should score fairly regardless of job structure
- This prevents structural bias"

**What You Should Understand:**
- How to handle missing data in calculations
- That edge cases matter for fairness
- Why we normalize based on what data actually exists
- That design choices affect outcomes

**Follow-up Topics:**
- What if a job has preferred but no required?
- Should we weight these differently?
- How do you decide what to do with missing dimensions?

---

### Question 12: How do you handle empty skill lists gracefully?

**What to Say:**
"Empty skills are important edge cases to handle:

**Case 1: Resume has no skills**
```python
if not candidate_skills:
    return {
        'success': False,
        'error': 'No skills found in resume analysis.'
    }
```
We return an error, but not a crash. User sees helpful message.

**Case 2: Job has no skills**
```python
if not required_skills and not preferred_skills:
    return {
        'success': False,
        'error': 'No skills found in job analysis.'
    }
```
Again, error with guidance instead of crash.

**Why this matters:**
- Bad input shouldn't crash system
- User gets actionable feedback: 'Resume analysis failed - try again'
- Not: 'Division by zero error at line 42' (useless)

**The flow:**
```
1. Check if resume analysis succeeded
2. Check if job analysis succeeded
3. Extract skills
4. Check if skills are non-empty
5. Only then proceed with matching
```

**Real scenario:**
- AI analysis sometimes returns empty skills (malformed resume, OCR fails)
- System should say: 'Please ensure your resume was analyzed correctly'
- Not crash silently

**Testing:**
```python
def test_error_empty_candidate_skills(self):
    result = match_resume_to_job(resume_with_no_skills, job_data)
    self.assertFalse(result['success'])
    self.assertIn('error', result)
```

We have dedicated tests for every edge case."

**What You Should Understand:**
- How to validate input before processing
- Why returning errors is better than crashing
- That edge cases need explicit handling
- Testing edge cases is crucial

**Follow-up Topics:**
- What other edge cases exist?
- How would you provide better error messages?
- Should system retry or suggest fixes?

---

### Question 13: How would you improve the matching system?

**What to Say:**
"There are several natural improvements for future commits:

**Phase 1: Better Skill Matching**
- Use embeddings (e.g., Word2Vec, BERT) to find similar skills
  - 'REST API' ≈ 'Web API' (detect semantic similarity)
  - Embed skills as vectors, find cosine similarity
  - Cost: More computation, need embedding model
  - Benefit: Catch real synonyms while avoiding false matches

- Build a skill ontology/graph
  - Java → OOP → Programming Fundamentals
  - Docker → Containerization → DevOps
  - Map relationships between skills

**Phase 2: Level-Aware Matching**
- Parse skill duration: 'Java' from resume might say '5 years'
- Parse job requirements: 'Java' from job might say 'Senior level'
- Score based on level match, not just presence/absence

**Phase 3: Context Understanding**
- Instead of just 'Java', extract: 'Java (Spring Boot, microservices, 3 years)'
- Match against: 'Java (backend systems)'
- More nuanced scoring

**Phase 4: Learning Gap Analysis**
- Python dev applying for Java role:
  - Current approach: 0% match
  - Better approach: Recognize transferable skills
  - Score: 'You have 60% transferable Python skills'

**Phase 5: Personalized Weighting**
- Let users/companies adjust weights
- 'For us, Docker is almost required' → increase preferred to 50%
- Different roles different weights

**Implementation priority:**
1. Embeddings (biggest impact, medium effort)
2. Skill ontology (big impact, high effort)
3. Level awareness (good impact, high effort)
4. Learning gap (nice-to-have, medium effort)"

**What You Should Understand:**
- How to think about incremental improvements
- The tradeoff between effort and benefit
- Different technologies for different problems
- That systems evolve, not perfect from start

**Follow-up Topics:**
- Which would you prioritize?
- How would you measure improvement success?
- What's the cost-benefit of each?

---

### Question 14: What is semantic similarity and how could embeddings improve this system?

**What to Say:**
"Semantic similarity is understanding that different words can mean the same thing:

**Current System:**
- 'REST API' ≠ 'Web API' (no match, even though similar)
- 'Database' ≠ 'SQL' (no match, but related)

**With Embeddings:**
We'd convert each skill to a high-dimensional vector (numbers):
```
'Java' → [0.23, -0.45, 0.67, ... (300 dimensions)]
'JavaScript' → [0.21, -0.43, 0.65, ...] (similar but distinct)
'Python' → [-0.12, 0.34, -0.28, ...] (different)

Calculate similarity using cosine similarity:
- Java vs JavaScript: 0.98 (very similar!) ← but we'd set threshold to 0.99
- Java vs Python: 0.73 (somewhat similar)
```

**Example Application:**
```
Resume: ['REST API', 'Microservices']
Job: ['Web APIs', 'Microservice Architecture']

With embeddings:
- 'REST API' ≈ 'Web APIs' (0.92 similarity) → match!
- 'Microservices' ≈ 'Microservice Architecture' (0.89) → match!
```

**How it works:**
1. Use pretrained embedding model (Word2Vec, GloVe, BERT)
2. Each skill → vector
3. For each candidate skill, find closest job skill
4. If similarity > threshold (e.g., 0.85), count as match
5. Adjust weighting by similarity score

**Pros:**
- ✅ Catches real synonyms and similar skills
- ✅ 'Machine Learning' ≈ 'ML' automatically
- ✅ More user-friendly matching

**Cons:**
- ❌ Requires ML model (added dependency)
- ❌ Slower (vector calculations)
- ❌ Might create false positives (need careful tuning)
- ❌ Less explainable ('why 0.85 threshold?')

**Example False Match Risk:**
```
Threshold too low:
- 'Java' → 0.70 similarity to 'JavaScript' → matched!
- User gets false positive, feels system is dumb

Solution: Threshold tuning, human review, logging
```

**Implementation:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
skill1_vec = model.encode('Java')
skill2_vec = model.encode('JavaScript')
similarity = util.cos_sim(skill1_vec, skill2_vec)
# Result: ~0.82 (too similar, but clearly different languages)
```

**Why we don't do this in Commit #6:**
- It's more complex
- We want to learn fundamentals first
- Can be added later when matching needs improvement"

**What You Should Understand:**
- What embeddings and vectors are
- How cosine similarity works
- The tradeoff between simple and sophisticated
- That semantic matching is a future enhancement

**Follow-up Topics:**
- What embedding model would you use?
- How would you set the threshold?
- How would you prevent false matches?
- What's the performance impact?

---

### Question 15: How could a vector database improve this system in the future?

**What to Say:**
"A vector database would enable powerful skills knowledge management:

**Current Limitation:**
- We match individual skills one-by-one
- No knowledge about skill relationships
- Can't answer: 'What is the skill hierarchy?' or 'What skills are related?'

**With Vector Database:**
```
Store every skill with its embedding:
- 'Java' → embedding + metadata {level, category, related_skills}
- 'Spring Boot' → embedding + metadata {requires: Java}
- 'OOP' → embedding + metadata {implied_by: [Java, C++, Python]}

Create relationships:
- Java ← requires ← Spring Boot (Spring Boot depends on Java)
- OOP ← implied ← Java (knowing Java means you know OOP)
- JavaScript ← sibling_language ← Java (both in 'programming languages')
```

**Real-World Benefits:**

1. **Smarter Matching:**
```
Candidate: [Java, Spring Boot]
Job: [Java, Spring Boot, Object-Oriented Design]

Query: 'Does candidate have OOP knowledge?'
Answer: 'Yes, Spring Boot requires OOP, so candidate has it'
New Match: 100% instead of 66%
```

2. **Personalized Learning Paths:**
```
'You're missing Docker'
Query DB: 'What skills does Docker build on?'
Answer: [Linux, Containers, DevOps]
Recommendation: 'Learn Containers first, then Docker'
```

3. **Skill Gap Analysis:**
```
Job wants: [Kubernetes, Microservices, Docker]
Candidate has: [Java, Spring Boot]
Query DB: 'Path from Spring Boot to Kubernetes?'
Answer: Docker → Containers → Orchestration → Kubernetes
Steps: 3-6 months of learning
Recommendation: 'You're 3 steps away'
```

4. **Salary Insights:**
```
Store: 'Java' embedding + {average_salary, demand_level, growth_rate}
Query: 'Most valuable next skill for Java developer?'
Answer: Kubernetes (highest salary gain, high demand)
```

**Implementation Example:**

```python
# Using Pinecone or Weaviate vector database
from pinecone import Pinecone

pc = Pinecone(api_key='...')
index = pc.Index('skills')

# Store skills with metadata
index.upsert([
    ('java', java_embedding, {'level': 'language', 'type': 'backend'}),
    ('spring-boot', spring_boot_embedding, {'level': 'framework', 'requires': 'java'}),
])

# Query: Find similar skills
results = index.query(java_embedding, top_k=5)
# → [spring-boot, kotlin, scala, groovy, clojure] (JVM languages)

# Recommendation engine
def get_next_skills(candidate_skills):
    query_vec = average_embeddings(candidate_skills)
    results = index.query(query_vec, top_k=10)
    return [s for s in results if s not in candidate_skills]
```

**Why wait for future commits:**
- Adds infrastructure complexity (another service)
- Current system is simple and fast
- Vector DBs shine when you need:
  - Complex relationships
  - Real-time similarity search at scale
  - Personalization

**When to add:**
- When users ask: 'What should I learn next?'
- When matching accuracy needs improvement
- When you have 10k+ skills in database
- When Commit #7 wants learning recommendations"

**What You Should Understand:**
- What vector databases are and when to use them
- How metadata enriches embeddings
- Use cases beyond matching (recommendations, insights)
- That databases are tools with tradeoffs
- Scalability and complexity considerations

**Follow-up Topics:**
- Which vector DB would you use?
- How would you populate the database?
- What metadata is most valuable?
- How would you keep it updated?
- Cost-benefit analysis?

---

## Summary: Key Takeaways for Interview

**What Interviewers Want to See:**

1. **Technical Understanding**
   - You understand algorithms, data structures, matching logic
   - You can explain the scoring formula clearly

2. **Design Thinking**
   - Why you chose deterministic over AI
   - Edge case handling
   - Separation of concerns

3. **Awareness of Limitations**
   - You know keyword matching isn't perfect
   - You have ideas for future improvements
   - You're honest about trade-offs

4. **Practical Engineering**
   - Tests prove your logic works
   - Error handling is thoughtful
   - Code is organized and maintainable

5. **Learning Mindset**
   - You know about embeddings, vector DBs, ontologies
   - You understand when to use each technique
   - You're thinking about the next iteration

**Interview Questions You Might Get:**

- ✅ "Walk me through your matching algorithm" → Show code, explain flow
- ✅ "Why use Python instead of LLM?" → Show tradeoffs (cost, speed, explainability)
- ✅ "How do you handle Java vs JavaScript?" → Show normalization + exact matching
- ✅ "What are the limitations?" → Be honest, show awareness
- ✅ "How would you improve it?" → Embeddings, ontologies, levels
- ✅ "Tell me about edge cases" → Empty skills, missing analyses, single dimension

**What NOT to Say:**

- ❌ "The system is perfect" (it's not - be honest)
- ❌ "I didn't think about X" (edge cases matter)
- ❌ "I'm not sure how it works" (know your code)
- ❌ "We use an LLM to score" (without discussing trade-offs)
- ❌ "I haven't tested it" (tests are critical)

---

## Study Guide

### 1. Understand the Code Deeply
- Read `ai/matcher.py` line by line
- Understand every function
- Know why functions exist

### 2. Know the Test Cases
- Read `tests/test_matcher.py`
- Understand what each test validates
- Know the edge cases

### 3. Study the Tradeoffs
- Why deterministic vs LLM?
- Why 70/30 weights?
- Why simple matching?

### 4. Prepare Examples
- Strong match scenario
- Weak match scenario
- Edge case scenario

### 5. Know the Architecture
- How does Flask route work?
- How does frontend interact?
- Why separation of concerns?

### 6. Think About Future
- Embeddings: how and when?
- Vector database: what for?
- Skill ontology: what would it look like?

---

Good luck with your interview! Remember: Show that you understand the problem, made deliberate design choices, handled edge cases, and are thinking about how to improve.
