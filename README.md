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
- **Resume-job skill matching** (NEW - Commit #6)
- **Match percentage calculation** (NEW - Commit #6)
- **Matched/missing skill identification** (NEW - Commit #6)
- **Skill recommendations** (NEW - Commit #6)

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

**Limitations (by design):**
- No semantic similarity: "REST API" ≠ "Web API" (different words = no match)
- No skill levels: "1 year Java" counts same as "10 years Java"
- No skill dependencies: "Java" ≠ "OOP" (even though OOP is implied)
- No synonyms: "Database" vs "SQL" treated as different

**Future improvements (in later commits):**
- Semantic matching using embeddings
- Skill level understanding
- Relationship mappings (Java → OOP)
- Synonym recognition

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
source .venv/bin/activate
python -m unittest tests.test_matcher -v
```

This runs 36 test cases covering:
- Skill normalization
- Exact and partial matching
- Case-insensitive matching
- Language distinction (Java vs JavaScript)
- Score calculation with various skill combinations
- Edge cases (empty skills, missing analyses)
- Full matching workflows
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
