# AI Interview Coach

AI Interview Coach is a Flask web application for practicing interview skills with focused, AI-assisted preparation.

## Current Features

- Basic landing page for AI Interview Coach
- Simple navigation and project introduction
- Flask route that renders the landing page
- Responsive HTML and CSS foundation

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

Create and activate a virtual environment, install the dependencies, and start Flask:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000/ in your browser.
