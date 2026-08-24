import os
import json

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from pypdf import PdfReader
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from ai.resume_analyzer import get_analyzer
from ai.job_analyzer import get_job_analyzer
from ai.matcher import match_resume_to_job
from ai.question_generator import generate_interview_questions
from ai.answer_evaluator import evaluate_answer
from analytics.interview_analytics import calculate_interview_performance

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "development-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
MAX_ANSWER_LENGTH = 10000


def extract_text_from_pdf(file_path):
    """Extract readable text from every page in a PDF file."""
    try:
        reader = PdfReader(file_path)

        if reader.is_encrypted:
            return ""
    except Exception:
        return ""

    extracted_pages = []
    for page in reader.pages:
        try:
            page_text = page.extract_text()
        except Exception:
            page_text = ""

        if page_text and page_text.strip():
            extracted_pages.append(page_text.strip())

    return "\n\n".join(extracted_pages)


@app.errorhandler(413)
def file_too_large(error):
    """Show a useful message when Flask rejects an oversized request."""
    flash("The resume is too large. Please choose a PDF smaller than 5 MB.", "error")
    return redirect(url_for("home"))


@app.route("/upload-resume", methods=["POST"])
def upload_resume():
    """
    Handle resume file upload and text extraction.
    Returns JSON with extracted text for the frontend to send for analysis.
    """
    uploaded_file = request.files.get("resume")

    if uploaded_file is None:
        flash("Please choose a PDF resume before uploading.", "error")
        return redirect(url_for("home"))

    if not uploaded_file.filename:
        flash("Please choose a PDF resume before uploading.", "error")
        return redirect(url_for("home"))

    if not uploaded_file.filename.lower().endswith(".pdf"):
        flash("Only PDF files are allowed.", "error")
        return redirect(url_for("home"))

    safe_filename = secure_filename(uploaded_file.filename)
    if not safe_filename or not safe_filename.lower().endswith(".pdf"):
        flash("That filename is not valid. Please rename the PDF and try again.", "error")
        return redirect(url_for("home"))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
    name, extension = os.path.splitext(safe_filename)
    counter = 1
    while os.path.exists(save_path):
        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{name}_{counter}{extension}"
        )
        counter += 1

    uploaded_file.save(save_path)
    extracted_text = extract_text_from_pdf(save_path)
    flash("Resume uploaded successfully.", "success")
    return render_template("index.html", extracted_text=extracted_text)


@app.route("/api/analyze-resume", methods=["POST"])
def analyze_resume_api():
    """
    API endpoint to analyze extracted resume text.
    Receives JSON with resume text, returns structured analysis.
    
    This separation (upload → extract → analyze) allows:
    1. Users to review extracted text before analysis
    2. Cleaner error handling for each step
    3. Users to retry analysis if the API fails
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        resume_text = data.get("resume_text", "").strip()
        
        if not resume_text:
            return jsonify({"success": False, "error": "No resume text provided"}), 400

        # Get the analyzer instance
        analyzer = get_analyzer()
        if not analyzer:
            return jsonify({
                "success": False,
                "error": "AI service is not configured. Please set OPENAI_API_KEY."
            }), 500

        # Analyze the resume
        result = analyzer.analyze_resume(resume_text)
        
        if result.get("success"):
            # Store resume analysis in session for matching
            session["resume_analysis"] = result
            session.modified = True
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        # Catch unexpected errors and don't expose details to frontend
        print(f"Error in /api/analyze-resume: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }), 500


@app.route("/api/analyze-job", methods=["POST"])
def analyze_job_api():
    """
    API endpoint to analyze a job description.
    
    Receives JSON with job title, company (optional), and description.
    Returns structured job analysis.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        job_title = data.get("job_title", "").strip()
        job_description = data.get("job_description", "").strip()
        company = data.get("company", "").strip() if data.get("company") else None

        # Get the analyzer instance
        analyzer = get_job_analyzer()
        if not analyzer:
            return jsonify({
                "success": False,
                "error": "AI service is not configured. Please set OPENAI_API_KEY."
            }), 500

        # Analyze the job description
        result = analyzer.analyze_job_description(job_title, job_description, company)
        
        if result.get("success"):
            # Store job analysis in session for matching
            session["job_analysis"] = result
            session.modified = True
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        # Catch unexpected errors
        print(f"Error in /api/analyze-job: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }), 500


@app.route("/api/match-resume", methods=["POST"])
def match_resume_api():
    """
    API endpoint to match resume skills against job requirements.
    
    This endpoint:
    1. Checks if both resume and job analyses exist in session
    2. Calls the matching engine
    3. Returns structured matching results
    
    Uses deterministic Python logic (no LLM calls) for speed, cost, and explainability.
    
    Flow:
    Resume Analysis (stored in session)
         +
    Job Analysis (stored in session)
         ↓
    Matching Engine (ai/matcher.py)
         ↓
    Matching Results (JSON)
    """
    try:
        # Check if analyses exist in session
        resume_analysis = session.get("resume_analysis")
        job_analysis = session.get("job_analysis")

        if not resume_analysis:
            return jsonify({
                "success": False,
                "error": "Resume has not been analyzed yet. Please analyze your resume first."
            }), 400

        if not job_analysis:
            return jsonify({
                "success": False,
                "error": "Job description has not been analyzed yet. Please analyze the job description first."
            }), 400

        # Call the matching engine
        matching_result = match_resume_to_job(resume_analysis, job_analysis)

        if matching_result.get("success"):
            return jsonify({
                "success": True,
                "result": matching_result.get("result")
            }), 200
        else:
            return jsonify(matching_result), 400

    except Exception as e:
        # Catch unexpected errors
        print(f"Error in /api/match-resume: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred during matching. Please try again."
        }), 500


@app.route("/api/generate-questions", methods=["POST"])
def generate_questions_api():
    """Generate questions from the analyses and matching data in the session."""
    try:
        data = request.get_json(silent=True) or {}
        resume_analysis = session.get("resume_analysis")
        job_analysis = session.get("job_analysis")

        if not resume_analysis:
            return jsonify({
                "success": False,
                "error": "Resume has not been analyzed yet. Please analyze your resume first.",
            }), 400
        if not job_analysis:
            return jsonify({
                "success": False,
                "error": "Job description has not been analyzed yet. Please analyze the job description first.",
            }), 400

        matching_result = match_resume_to_job(resume_analysis, job_analysis)
        if not matching_result.get("success"):
            return jsonify(matching_result), 400

        result = generate_interview_questions(
            resume_analysis.get("analysis"),
            job_analysis.get("analysis"),
            matching_result.get("result"),
            data.get("interview_type"),
            data.get("difficulty"),
            data.get("number_of_questions"),
        )
        if result.get("success"):
            questions = [
                {"id": index + 1, **question}
                for index, question in enumerate(result.get("questions", []))
            ]
            session["generated_questions"] = questions
            session["generated_interview_config"] = {
                "interview_type": data.get("interview_type"),
                "difficulty": data.get("difficulty"),
                "total_questions": len(questions),
            }
            result["questions"] = questions
        return jsonify(result), 200 if result.get("success") else 400
    except Exception:
        return jsonify({
            "success": False,
            "error": "Unable to generate interview questions right now. Please try again.",
        }), 500


@app.route("/start-interview", methods=["POST"])
def start_interview():
    """Start a fresh interview from the server-owned generated questions."""
    questions = session.get("generated_questions")
    config = session.get("generated_interview_config")
    if not isinstance(questions, list) or not questions or not isinstance(config, dict):
        flash("Please generate interview questions first.", "error")
        return redirect(url_for("home"))

    session["interview"] = {
        "questions": questions,
        "current_index": 0,
        "answers": [],
        "interview_type": config.get("interview_type"),
        "difficulty": config.get("difficulty"),
        "total_questions": len(questions),
    }
    session.pop("completed_interview", None)
    return redirect(url_for("interview"))


@app.route("/interview", methods=["GET"])
def interview():
    """Display the current question from the active interview session."""
    interview_state = session.get("interview")
    if not _valid_interview_state(interview_state):
        flash("Please start an interview first.", "error")
        return redirect(url_for("home"))

    current_index = interview_state["current_index"]
    if current_index >= len(interview_state["questions"]):
        return redirect(url_for("finish_interview"))

    return render_template(
        "interview.html",
        question=interview_state["questions"][current_index],
        current_index=current_index,
        total_questions=len(interview_state["questions"]),
        answer=_answer_for_question(interview_state, interview_state["questions"][current_index]["id"]),
        error=None,
    )


@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    """Validate and save one answer, then advance to the next question."""
    interview_state = session.get("interview")
    if not _valid_interview_state(interview_state):
        flash("Please start an interview first.", "error")
        return redirect(url_for("home"))

    current_question = interview_state["questions"][interview_state["current_index"]]
    question_id = request.form.get("question_id", "")
    answer = request.form.get("answer", "")
    if str(current_question["id"]) != question_id:
        return _render_interview_error(interview_state, "That question is no longer current. Please continue with the current question.", 400)
    if not answer.strip():
        return _render_interview_error(interview_state, "Please provide an answer before continuing.", 400)
    if len(answer) > MAX_ANSWER_LENGTH:
        return _render_interview_error(interview_state, "Your answer is too long. Please keep it under 10,000 characters.", 400)
    if _answer_for_question(interview_state, current_question["id"]) is not None:
        return _render_interview_error(interview_state, "This answer was already submitted. Please continue with the current question.", 400)

    interview_state["answers"].append({
        "question_id": current_question["id"],
        "question": current_question["question"],
        "answer": answer.strip(),
        "category": current_question["category"],
        "difficulty": current_question["difficulty"],
        "topic": current_question.get("topic", "Unspecified topic"),
    })
    session["interview"] = interview_state
    evaluation_result = evaluate_answer(
        current_question["question"],
        answer.strip(),
        current_question["category"],
        current_question["difficulty"],
        current_question["topic"],
        _evaluation_job_context(),
    )
    saved_answer = interview_state["answers"][-1]
    if evaluation_result.get("success"):
        saved_answer["evaluation"] = evaluation_result["evaluation"]
        evaluation_error = None
    else:
        saved_answer["evaluation_error"] = evaluation_result.get(
            "error", "Your answer was saved, but we could not evaluate it right now."
        )
        evaluation_error = "Your answer was saved, but we couldn't evaluate it right now. You can continue."
    session["interview"] = interview_state
    return _render_interview_result(interview_state, evaluation_error), 200


@app.route("/next-question", methods=["POST"])
def next_question():
    """Advance only after the current answer has been saved and evaluated or skipped."""
    interview_state = session.get("interview")
    if not _valid_interview_state(interview_state):
        flash("Please start an interview first.", "error")
        return redirect(url_for("home"))
    current_question = interview_state["questions"][interview_state["current_index"]]
    if _answer_for_question(interview_state, current_question["id"]) is None:
        return _render_interview_error(interview_state, "Submit an answer before continuing.", 400)
    interview_state["current_index"] += 1
    if interview_state["current_index"] >= len(interview_state["questions"]):
        session["completed_interview"] = interview_state
        session.pop("interview", None)
        return redirect(url_for("finish_interview"))
    session["interview"] = interview_state
    return redirect(url_for("interview"))


@app.route("/finish-interview", methods=["GET"])
def finish_interview():
    """Display the submitted answers without evaluating them."""
    completed = session.get("completed_interview")
    if not _valid_interview_state(completed) or completed["current_index"] < len(completed["questions"]):
        flash("Complete an interview before viewing its summary.", "error")
        return redirect(url_for("home"))
    return render_template(
        "interview_summary.html",
        answers=completed["answers"],
        total_questions=len(completed["questions"]),
    )


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Render deterministic performance analytics for the completed interview."""
    completed = session.get("completed_interview")
    if not _valid_interview_state(completed) or completed["current_index"] < len(completed["questions"]):
        flash("No completed interview is available. Complete an interview to see your performance dashboard.", "error")
        return redirect(url_for("home"))
    performance = calculate_interview_performance(
        completed.get("answers", []),
        total_questions=len(completed["questions"]),
    )
    return render_template("dashboard.html", performance=performance)


def _valid_interview_state(interview_state):
    """Check the minimum server-owned shape required by interview routes."""
    return (
        isinstance(interview_state, dict)
        and isinstance(interview_state.get("questions"), list)
        and bool(interview_state["questions"])
        and isinstance(interview_state.get("answers"), list)
        and isinstance(interview_state.get("current_index"), int)
        and 0 <= interview_state["current_index"] <= len(interview_state["questions"])
    )


def _answer_for_question(interview_state, question_id):
    """Find an existing answer by stable question ID."""
    return next(
        (answer for answer in interview_state["answers"] if answer.get("question_id") == question_id),
        None,
    )


def _render_interview_error(interview_state, error, status_code):
    current_index = interview_state["current_index"]
    question = interview_state["questions"][current_index]
    return render_template(
        "interview.html",
        question=question,
        current_index=current_index,
        total_questions=len(interview_state["questions"]),
        answer=_answer_for_question(interview_state, question["id"]),
        error=error,
        evaluation=None,
        can_continue=False,
    ), status_code


def _render_interview_result(interview_state, error=None):
    """Render saved answer evaluation before allowing the next question."""
    current_index = interview_state["current_index"]
    question = interview_state["questions"][current_index]
    saved_answer = _answer_for_question(interview_state, question["id"])
    return render_template(
        "interview.html",
        question=question,
        current_index=current_index,
        total_questions=len(interview_state["questions"]),
        answer=saved_answer,
        error=error,
        evaluation=saved_answer.get("evaluation") if saved_answer else None,
        can_continue=True,
    )


def _evaluation_job_context():
    """Return only job fields useful for evaluating the current answer."""
    job_analysis = session.get("job_analysis", {})
    return job_analysis.get("analysis", {}) if isinstance(job_analysis, dict) else {}


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
