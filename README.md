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
- **Job description analysis** (NEW - Commit #5)
- **Required/preferred skill extraction** (NEW - Commit #5)
- **Job requirement extraction** (NEW - Commit #5)

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
- **`ai/resume_analyzer.py`**: OpenAI API communication and response parsing
- **`templates/index.html`**: User interface
- **`static/js/script.js`**: Frontend analysis handling and loading states
- **`static/css/style.css`**: Styling

The analyzer is separated from the Flask app to keep code modular and maintainable.

## Environment Variables

Create a `.env` file in the project root (see `.env.example` for template):

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI analysis)
- `SECRET_KEY`: Flask secret key (optional, defaults to development key)
- `FLASK_DEBUG`: Set to `True` for development (optional) text,
so they show a message explaining that OCR may be needed in a future commit.
