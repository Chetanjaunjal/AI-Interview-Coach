# AI Interview Coach

AI Interview Coach is a Flask web application for practicing interview skills with focused, AI-assisted preparation.

## Current Features

- Flask application
- Resume PDF upload
- PDF validation
- 5 MB upload limit
- Secure filename handling
- PDF text extraction
- **AI-powered resume analysis** (Commit #4)
- **Structured information extraction** (Commit #4)
- **Clean analysis display** (Commit #4)
- **Job description analysis** (Commit #5)
- **Required/preferred skill extraction** (Commit #5)
- **Job requirement extraction** (Commit #5)
- **Resume-job skill matching** (Commit #6)
- **Match percentage calculation** (Commit #6)
- **Matched/missing skill identification** (Commit #6)
- **Skill recommendations** (Commit #6)
- **Semantic skill matching using embeddings** (NEW - Commit #7)
- **Hybrid exact + semantic matching** (NEW - Commit #7)
- **Semantic similarity scoring** (NEW - Commit #7)

## Planned Features

- Resume upload and analysis
- Target job and interview type selection
- AI-generated interview questions
- Practice answers and chatbot-style interaction
- AI feedback and scoring
- Interview history and an improvement roadmap
- User authentication and a database

## Technology Stack

- Python
- Flask
- HTML
- CSS
- JavaScript
- OpenAI API
- Git and GitHub

## Project Structure

```text
AI-Interview-Coach/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── ai/
├── database/
├── uploads/
└── tests/
```

## Run Locally
### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
```

Then edit `.env` and replace `your_api_key_here` with your actual OpenAI API key:

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

**Get your API key**: Sign up at https://platform.openai.com/account/api-keys

**Important**: Never commit `.env` to GitHub. It's already in `.gitignore`.

### 4. Start the application

```bash
python app.py
```

Then open http://127.0.0.1:5000/ in your browser.

## How to Use

1. **Upload Resume**: Choose a PDF resume smaller than 5 MB
2. **Review Extracted Text**: The app extracts text from your PDF for preview
3. **Analyze Resume with AI**: Click "Analyze Resume with AI" to get structured analysis
4. **View Resume Results**: See extracted information including name, email, skills, education, experience, projects, certifications, and achievements
5. **Analyze Job Description**: Enter a job title and paste a job description
6. **View Job Results**: See required skills, preferred skills, programming languages, frameworks, tools, databases, education, experience, responsibilities, qualifications, and keywords

## Job Description Analysis

The job analyzer extracts structured information from job postings:

```
Job Description (text)
    ↓
LLM Analysis (OpenAI API)
    ↓
Structured JSON (required skills, preferred skills, frameworks, etc.)
    ↓
Display Results (formatted on page)
```

This enables future features like:
- Resume-to-job skill matching
- Identifying skill gaps
- Prioritizing which skills to focus on
- Generating targeted interview questions

## Resume-Job Matching System (Commit #6)

The matching system compares your resume skills with job requirements to determine how well you fit a role.

### How It Works

```
Resume Analysis (AI-structured data)
    ↓
Job Analysis (AI-structured data)
    ↓
Skill Normalization (lowercase, trim whitespace)
    ↓
Matching Engine (Python logic - NO additional LLM calls)
    ↓
Match Results:
  ├─ Match Percentage (0-100%)
  ├─ Matched Required Skills
  ├─ Missing Required Skills
  ├─ Matched Preferred Skills
  ├─ Missing Preferred Skills
  ├─ Additional Candidate Skills
  └─ Personalized Recommendations
```

### Matching Algorithm

The matcher uses **deterministic Python logic** (not AI) for speed, cost, and explainability:

1. **Skill Extraction**: Pulls skills from AI-analyzed resume and job
2. **Normalization**: Converts all skills to lowercase and trims whitespace
   - "Java", "JAVA", "  java  " all become "java"
   - Prevents false misses due to formatting
3. **Comparison**: Uses exact string matching on normalized skills
   - Java ≠ JavaScript (correctly distinguished)
   - React ≠ React Native (correctly distinguished)
4. **Scoring**: Weighted formula favoring required over preferred skills
   - Required skills: 70% weight
   - Preferred skills: 30% weight
   - Example: 100% required + 0% preferred = 70% overall match

### Score Calculation

```
If job has both required and preferred skills:
  Overall % = (Required Score × 0.70) + (Preferred Score × 0.30)

If job has only required skills:
  Overall % = Required Score (100% scale)

If job has only preferred skills:
  Overall % = Preferred Score (100% scale)

Where:
  Required Score = (Matched Required) / (Total Required)
  Preferred Score = (Matched Preferred) / (Total Preferred)
```

### Why Deterministic Matching?

**Advantages over AI-based matching:**
- ✅ Fast: No LLM API calls = instant results
- ✅ Cheap: No token usage = reduced costs
- ✅ Explainable: You can see exactly why a skill matched/didn't match
- ✅ Reproducible: Same input always produces same output
- ✅ Debuggable: Easy to understand and fix bugs

**Limitations (by design in Commit #6):**
- No semantic similarity: "REST API" ≠ "Web API" (different words = no match)
- No skill levels: "1 year Java" counts same as "10 years Java"
- No skill dependencies: "Java" ≠ "OOP" (even though OOP is implied)
- No synonyms: "Database" vs "SQL" treated as different

**These limitations are addressed in Commit #7 with semantic matching.**

---

## Semantic Skill Matching with Embeddings (Commit #7)

Commit #7 enhances the matching system with **semantic understanding** using embeddings while preserving the reliability of exact matching.

### What Are Embeddings?

An embedding is a way to represent text as a list of numbers that captures its meaning.

```
Text:      "REST API development"
           ↓ (Convert to numbers)
Embedding: [0.234, -0.891, 0.456, 0.123, -0.234, ..., 0.456]
           (384 numbers for all-MiniLM-L6-v2 model)
```

Similar concepts have similar embeddings:
- "REST API" and "RESTful API" → very close numbers
- "JavaScript" → very different numbers

### How Semantic Matching Works

```
Resume Skill: "REST API development"
Job Skill: "RESTful API"

Step 1: Convert to embeddings
  Resume: [0.234, -0.891, 0.456, ...]
  Job:    [0.245, -0.875, 0.468, ...]

Step 2: Calculate similarity (cosine similarity)
  Similarity: 0.87 (on a scale of 0 to 1)

Step 3: Compare to threshold (default: 0.75)
  0.87 > 0.75 → MATCH! ✓
```

### Hybrid Matching: Best of Both Worlds

```
Resume Skill
    ↓
    ├─ Try Exact Matching First
    │   └─ If match found → Record as "exact" (100% confidence)
    │
    └─ If no exact match, Try Semantic Matching
        ├─ Convert to embeddings
        ├─ Calculate similarity
        └─ If similarity > threshold → Record as "semantic" (87% confidence, for example)
```

**Why hybrid?**
- Exact matches are most reliable (zero false positives)
- Semantic matching catches variations and synonyms
- Semantic matches include confidence scores (similarity %)
- Users see which type of match was made

### Real Examples

| Candidate | Job | Exact Match | Semantic Match | Result |
|-----------|-----|-------------|----------------|--------|
| REST API development | RESTful API | ❌ No | ✅ Yes (87%) | MATCH |
| OOP | Object Oriented Programming | ❌ No | ✅ Yes (92%) | MATCH |
| SQL | SQL | ✅ Yes | N/A | MATCH |
| Java | JavaScript | ❌ No | ❌ No (45% < 0.75) | NO MATCH ✓ |
| Python | PyTorch | ❌ No | ❌ No (62% < 0.75) | NO MATCH ✓ |

### The Embedding Model

We use **`all-MiniLM-L6-v2`** from Sentence Transformers:

- **Lightweight**: Only 384 dimensions (vs 1536 for larger models)
- **Fast**: Runs on CPU without GPU
- **Pretrained**: Already trained on billions of sentences
- **General-purpose**: Works well for diverse skill descriptions
- **Free and local**: No API calls needed, runs entirely on your computer

### Similarity Threshold

The threshold determines when to consider skills as matching:

```
Threshold = 0.75 (default, can be adjusted)

Similarity Score    Decision
     0.0-0.50      Not similar
     0.50-0.75     Somewhat similar (below threshold)
     0.75-1.0      Similar match (above threshold)
```

**Why a threshold?**
- Too low (0.50): Many false positives (Java matches JavaScript)
- Too high (0.95): Many false negatives (REST API doesn't match RESTful API)
- Sweet spot (0.75): Balances false positives and false negatives

You can adjust the threshold in `ai/semantic_matcher.py`:
```python
SEMANTIC_SIMILARITY_THRESHOLD = 0.75  # Change this value
```

### Performance Optimization

To avoid redundant embeddings calculations:

```python
# Inefficient: Recalculates embeddings for every comparison
for job_skill in job_skills:
    for candidate_skill in candidate_skills:
        similarity = calculate_semantic_similarity(job_skill, candidate_skill)

# With 20 job skills × 20 candidate skills = 400 calculations!

# Efficient: Pre-compute once, reuse many times
candidate_embeddings = precompute_embeddings(candidate_skills)
for job_skill in job_skills:
    match = find_best_semantic_match(
        job_skill,
        candidate_skills,
        pre_computed_embeddings=candidate_embeddings
    )

# Only 40 calculations (20 + 20)
# 10x faster!
```

### Key Files for Semantic Matching

- **`ai/semantic_matcher.py`**: Embedding and similarity calculations
  - `get_embedding_model()`: Loads the sentence transformer model
  - `generate_embedding()`: Converts text to embedding
  - `calculate_cosine_similarity()`: Measures vector similarity
  - `calculate_semantic_similarity()`: Main similarity function
  - `find_best_semantic_match()`: Finds best match in candidates
  - `precompute_embeddings()`: Optimization for multiple comparisons
  
- **`ai/matcher.py`**: Updated hybrid matching logic
  - `find_hybrid_matches()`: Combines exact + semantic matching
  - `match_resume_to_job()`: Now returns match types and scores
  
- **`tests/test_semantic_matcher.py`**: Semantic matching tests
  - 18 test cases for similarity calculations
  - Tests false positive prevention (Java vs JavaScript)
  - Threshold behavior tests
  
- **`tests/test_hybrid_matcher.py`**: Hybrid integration tests
  - 15 test cases for combined exact + semantic matching
  - Full pipeline testing

### Limitations of Embeddings

**Embeddings are not magic—they have limitations:**

1. **Domain-specific limitations**: The model is trained on general text, not specialized technical domains
2. **Surprising similarities**: The model might assign unexpected similarity scores
3. **Spelling sensitivity**: Typos significantly affect embeddings
4. **Model quality**: Depends on the quality of training data
5. **Probabilistic**: Not mathematically "correct," but statistically good enough

**Examples of unexpected behavior:**
```python
similarity("Python", "Perl")       # Might be 0.65
similarity("Java", "JavaScript")   # Might be 0.52 (just below threshold!)
similarity("SQL", "NoSQL")         # Might be 0.58
```

**Why still use embeddings then?**
- They catch many real skill variations (REST API vs RESTful API)
- They reduce false negatives (missed valid skills)
- They maintain a threshold to reduce false positives
- Combined with exact matching, they're much more reliable

### Testing the System

Run the semantic matching tests:

```bash
# Test semantic similarity calculations
python -m pytest tests/test_semantic_matcher.py -v

# Test hybrid matching integration
python -m pytest tests/test_hybrid_matcher.py -v

# Run all tests
python -m pytest tests/ -v
```

### Future Improvements

Possible enhancements (not in Commit #7):
- **Better models**: Use domain-specific embedding models for tech skills
- **Skill ontology**: Build a graph of skill relationships
- **Context awareness**: Consider job domain when matching
- **Entity recognition**: Better identify skills vs frameworks vs tools
- **Skill aliases**: Manually curated lists of known synonyms
- **Vector databases**: Cache embeddings for faster comparisons
- **RAG (Retrieval-Augmented Generation)**: Hybrid LLM + embedding approach

---

### Key Files for Matching

- **`ai/matcher.py`**: Core matching engine
  - `normalize_skill()`: Normalizes skill names
  - `find_matching_skills()`: Compares candidate vs job skills
  - `calculate_match_percentage()`: Weighted scoring formula
  - `generate_recommendations()`: Creates personalized advice
  - `match_resume_to_job()`: Main matching function
- **`tests/test_matcher.py`**: 36 comprehensive test cases

### Using the Matching System

1. Upload and analyze your resume
2. Enter and analyze a job description
3. Click "Match Resume to Job" button
4. View your match percentage and skill breakdown
5. Read personalized recommendations for growth

### Running Tests

Test the matching system:

```bash
source venv/bin/activate

# Test exact matching (Commit #6)
python -m unittest tests.test_matcher -v

# Test semantic matching (Commit #7)
python -m pytest tests/test_semantic_matcher.py -v

# Test hybrid matching integration (Commit #7)
python -m pytest tests/test_hybrid_matcher.py -v

# Run all tests
python -m pytest tests/ -v
```

**Test coverage:**
- Commit #6: 36 test cases for exact matching
- Commit #7: 18 test cases for semantic similarity
- Commit #7: 15 test cases for hybrid matching
- Total: 69 comprehensive test cases
Resume analysis using OpenAI API
- **`ai/job_analyzer.py`**: Job description analysis using OpenAI API
- **`templates/index.html`**: User interface
- **`static/js/script.js`**: Frontend analysis handling and loading states
- **`static/css/style.css`**: Styling

Analyzers are separated from Flask to keep code modular and test
Resume PDF (upload)
    ↓
PDF Text Extraction (pypdf)
    ↓
Extracted Text (preview)
    ↓
LLM Analysis (OpenAI API)
    ↓
Structured JSON (name, email, skills, etc.)
    ↓
Display Results (formatted on page)
```

### Code Structure

- **`app.py`**: Flask routes and PDF handling
- **`ai/resume_analyzer.py`**: Resume analysis using OpenAI API
- **`ai/job_analyzer.py`**: Job description analysis using OpenAI API
- **`ai/matcher.py`**: Resume-to-job skill matching (Commit #6, NEW)
- **`templates/index.html`**: User interface
- **`static/js/script.js`**: Frontend analysis and matching handling
- **`static/css/style.css`**: Styling
- **`tests/test_matcher.py`**: Comprehensive matching tests (Commit #6, NEW)

The analyzer is separated from the Flask app to keep code modular and maintainable.

## Environment Variables

Create a `.env` file in the project root (see `.env.example` for template):

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI analysis)
- `SECRET_KEY`: Flask secret key (optional, defaults to development key)
- `FLASK_DEBUG`: Set to `True` for development (optional) text,
so they show a message explaining that OCR may be needed in a future commit.
