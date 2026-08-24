import os
import json
import logging
import time
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from pypdf import PdfReader
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from ai.resume_analyzer import get_analyzer
from ai.job_analyzer import get_job_analyzer
from ai.matcher import match_resume_to_job
from ai.question_generator import generate_interview_questions
from ai.answer_evaluator import evaluate_answer
from ai.resume_tailor import analyze_resume_keywords, calculate_ats_score, tailor_resume
from analytics.interview_analytics import calculate_interview_performance
from analytics.weakness_detector import detect_weak_topics
from analytics.job_preparation import build_job_interview_plan
from analytics.roadmap import build_daily_plan, build_roadmap
from analytics.readiness import calculate_readiness
from ai.roadmap_explainer import explain_roadmap
from utils.pdf_export import resume_to_pdf
from flask import Response
from config import Config
from database.db import (
    DatabaseError,
    create_user,
    create_job,
    create_resume,
    create_tailored_resume,
    delete_user_interview,
    get_user_by_email,
    get_user_by_id,
    get_user_cover_letter_count,
    get_user_interview,
    get_user_interviews,
    get_user_job,
    get_user_jobs,
    get_user_resume,
    get_user_resumes,
    get_user_tailored_resume,
    get_user_tailored_resumes,
    init_database,
    save_completed_interview,
    update_resume_analysis,
    update_job_matching,
    delete_user_account,
    export_user_data,
)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
MAX_ANSWER_LENGTH = app.config["MAX_ANSWER_LENGTH"]
app.logger.setLevel(logging.INFO)
_ai_request_times = {}
init_database(app)


def rate_limited(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        now = time.monotonic()
        key = (request.remote_addr or "unknown", request.endpoint)
        recent = [stamp for stamp in _ai_request_times.get(key, []) if now - stamp < 60]
        if len(recent) >= app.config["MAX_AI_REQUESTS_PER_MINUTE"]:
            return jsonify({"success": False, "error": "Too many AI requests. Please try again shortly."}), 429
        recent.append(now)
        _ai_request_times[key] = recent
        return view(*args, **kwargs)
    return wrapped_view


def get_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    try:
        return get_user_by_id(user_id, app)
    except (DatabaseError, ValueError):
        session.pop("user_id", None)
        return None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


def _valid_email(email):
    email = (email or "").strip().lower()
    return bool(email and "@" in email and "." in email.split("@")[-1] and not email.startswith("@") and not email.endswith("@"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")
        if not name:
            flash("Name is required.", "error")
        elif not _valid_email(email):
            flash("Please enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif password != confirmation:
            flash("Passwords do not match.", "error")
        else:
            try:
                create_user(name, email, generate_password_hash(password), app)
            except ValueError:
                flash("An account with this email already exists.", "error")
            except DatabaseError:
                flash("We could not create your account right now.", "error")
            else:
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        try:
            user = get_user_by_email(email, app) if email and password else None
        except DatabaseError:
            user = None
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            next_url = request.args.get("next", "")
            return redirect(next_url if next_url.startswith("/") and not next_url.startswith("//") else url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    user = get_current_user()
    return render_template("profile.html", user=user, user_counts={"interviews": len(get_user_interviews(user["id"], app)), "resumes": len(get_user_resumes(user["id"], app)), "jobs": len(get_user_jobs(user["id"], app)), "cover_letters": get_user_cover_letter_count(user["id"], app)})


@app.route("/export-data")
@login_required
def export_data():
    try:
        data = export_user_data(session["user_id"], app)
    except DatabaseError:
        flash("Your data could not be exported right now.", "error")
        return redirect(url_for("profile"))
    return Response(json.dumps(data, indent=2), mimetype="application/json", headers={"Content-Disposition": "attachment; filename=interview-coach-data.json"})


@app.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    if request.form.get("confirmation") != "DELETE":
        flash("Type DELETE to confirm account deletion.", "error")
        return redirect(url_for("profile"))
    try:
        delete_user_account(session["user_id"], app)
    except (DatabaseError, ValueError):
        flash("Your account could not be deleted right now.", "error")
        return redirect(url_for("profile"))
    session.clear()
    return redirect(url_for("home"))


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


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


@app.errorhandler(500)
def internal_error(error):
    app.logger.error("Unhandled application error", exc_info=True)
    return render_template("500.html"), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/upload-resume", methods=["POST"])
@login_required
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
    if extracted_text:
        try:
            session["resume_id"] = create_resume(session["user_id"], safe_filename, extracted_text, app=app)
        except DatabaseError:
            flash("The resume was read but could not be saved.", "error")
    flash("Resume uploaded successfully.", "success")
    return render_template("index.html", extracted_text=extracted_text)


@app.route("/api/analyze-resume", methods=["POST"])
@login_required
@rate_limited
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
            try:
                if session.get("resume_id"):
                    update_resume_analysis(session["resume_id"], session["user_id"], result.get("analysis", {}), app)
                else:
                    session["resume_id"] = create_resume(session["user_id"], "analyzed-resume", resume_text, result.get("analysis", {}), app)
            except (DatabaseError, ValueError):
                return jsonify({"success": False, "error": "The resume was analyzed but could not be saved."}), 500
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
@login_required
@rate_limited
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
            try:
                job_id = create_job(session["user_id"], job_title, company, job_description, result.get("analysis", result), app)
                session["job_id"] = job_id
            except (DatabaseError, ValueError):
                return jsonify({"success": False, "error": "The job was analyzed but could not be saved."}), 500
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
@login_required
@rate_limited
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
            session["matching_result"] = matching_result.get("result", {})
            if session.get("job_id"):
                update_job_matching(session["job_id"], session["user_id"], matching_result.get("result", {}), app)
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
@login_required
@rate_limited
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
                "job_id": session.get("job_id"),
                "job_title": session.get("job_analysis", {}).get("analysis", {}).get("job_title"),
            }
            session["matching_result"] = matching_result.get("result", {})
            result["questions"] = questions
        return jsonify(result), 200 if result.get("success") else 400
    except Exception:
        return jsonify({
            "success": False,
            "error": "Unable to generate interview questions right now. Please try again.",
        }), 500


@app.route("/start-interview", methods=["POST"])
@login_required
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
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "practice_topic": config.get("practice_topic"),
        "previous_score": config.get("previous_score"),
        "job_id": config.get("job_id"),
        "job_title": config.get("job_title"),
        "interview_mode": config.get("interview_mode", "text"),
    }
    session.pop("completed_interview", None)
    return redirect(url_for("interview"))


@app.route("/voice-interview", methods=["GET"])
@login_required
def voice_interview():
    try:
        jobs = get_user_jobs(session["user_id"], app)
    except DatabaseError:
        jobs = []
    return render_template("voice_interview.html", jobs=jobs)


@app.route("/voice-interview/start", methods=["POST"])
@login_required
@rate_limited
def start_voice_interview():
    interview_type = request.form.get("interview_type", "technical").lower()
    difficulty = request.form.get("difficulty", "medium").lower()
    count = request.form.get("number_of_questions", type=int) or 5
    if interview_type not in {"technical", "hr", "behavioral", "mixed"}:
        interview_type = "technical"
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"
    if count not in {5, 10, 15}:
        count = 5
    resume = session.get("resume_analysis") or {"success": True, "analysis": {"skills": []}}
    job = session.get("job_analysis") or {"success": True, "analysis": {"job_title": "Interview practice"}}
    matching = session.get("matching_result") or {"matched_required_skills": [], "missing_required_skills": []}
    selected_job_id = request.form.get("job_id", type=int)
    if selected_job_id:
        try:
            selected_job = get_user_job(selected_job_id, session["user_id"], app)
        except (DatabaseError, ValueError):
            selected_job = None
        if selected_job:
            job = {"success": True, "analysis": selected_job["analyzed_data"]}
            session["job_id"] = selected_job["id"]
            session["job_analysis"] = job
            selected_matching = match_resume_to_job(resume, job) if resume.get("analysis", {}).get("skills") else None
            matching = selected_matching.get("result", {}) if selected_matching and selected_matching.get("success") else {"matched_required_skills": [], "missing_required_skills": job["analysis"].get("required_skills", [])}
        else:
            matching = session.get("matching_result") or {"matched_required_skills": [], "missing_required_skills": []}
    result = generate_interview_questions(resume.get("analysis", {}), job.get("analysis", {}), matching, interview_type, difficulty, count)
    if not result.get("success"):
        flash(result.get("error", "Generate interview questions before starting voice mode."), "error")
        return redirect(url_for("voice_interview"))
    session["generated_questions"] = [{"id": index + 1, **question} for index, question in enumerate(result["questions"])]
    session["generated_interview_config"] = {"interview_type": interview_type, "difficulty": difficulty, "total_questions": count, "interview_mode": "voice", "job_id": session.get("job_id"), "job_title": job.get("analysis", {}).get("job_title")}
    return redirect(url_for("start_interview"), code=307)


@app.route("/practice", methods=["GET"])
@login_required
def practice():
    try:
        analysis = detect_weak_topics(session["user_id"], app)
    except DatabaseError:
        flash("Practice recommendations are temporarily unavailable.", "error")
        analysis = {"weak_topics": [], "has_data": False}
    return render_template("practice.html", analysis=analysis)


@app.route("/practice/<topic>", methods=["POST"])
@login_required
@rate_limited
def start_practice(topic):
    try:
        analysis = detect_weak_topics(session["user_id"], app)
    except DatabaseError:
        flash("Practice recommendations are temporarily unavailable.", "error")
        return redirect(url_for("practice"))
    selected = next((item for item in analysis["weak_topics"] if item["topic"].casefold() == topic.casefold()), None)
    if selected is None:
        return render_template("interview_not_found.html"), 404
    difficulty = request.form.get("difficulty", "medium").lower()
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"
    count = request.form.get("number_of_questions", type=int) or 5
    if count not in {5, 10, 15}:
        count = 5
    result = generate_interview_questions(
        session.get("resume_analysis", {}).get("analysis", {}) or {"skills": [selected["topic"]]},
        session.get("job_analysis", {}).get("analysis", {}) or {"job_title": "Targeted practice"},
        session.get("matching_result", {}) or {"matched_required_skills": [selected["topic"]]},
        "technical",
        difficulty,
        count,
        selected["topic"],
        selected.get("missing_concepts", []),
    )
    if not result.get("success"):
        flash(result.get("error", "Unable to generate practice questions."), "error")
        return redirect(url_for("practice"))
    questions = [{"id": index + 1, **question} for index, question in enumerate(result["questions"])]
    session["generated_questions"] = questions
    session["generated_interview_config"] = {"interview_type": "practice", "difficulty": difficulty, "total_questions": len(questions), "practice_topic": selected["topic"], "previous_score": selected["average_score"]}
    return redirect(url_for("start_interview"), code=307)


@app.route("/jobs", methods=["GET"])
@login_required
def jobs():
    try:
        saved_jobs = get_user_jobs(session["user_id"], app)
    except DatabaseError:
        flash("Your saved jobs are temporarily unavailable.", "error")
        saved_jobs = []
    return render_template("jobs.html", jobs=saved_jobs)


@app.route("/jobs/<job_id>", methods=["GET"])
@login_required
def job_detail(job_id):
    try:
        job = get_user_job(job_id, session["user_id"], app)
    except (DatabaseError, ValueError):
        job = None
    if job is None:
        return render_template("interview_not_found.html"), 404
    return render_template("job_detail.html", job=job)


@app.route("/job-prep", methods=["GET", "POST"])
@login_required
@rate_limited
def job_prep():
    try:
        saved_jobs = get_user_jobs(session["user_id"], app)
    except DatabaseError:
        flash("Your saved jobs are temporarily unavailable.", "error")
        saved_jobs = []
    if request.method == "GET":
        return render_template("job_prep.html", jobs=saved_jobs)
    job_id = request.form.get("job_id", "")
    try:
        job = get_user_job(job_id, session["user_id"], app)
    except (DatabaseError, ValueError):
        job = None
    if job is None:
        flash("Please choose one of your saved jobs.", "error")
        return redirect(url_for("job_prep"))
    difficulty = request.form.get("difficulty", "medium").lower()
    count = request.form.get("number_of_questions", type=int) or 10
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"
    if count not in {5, 10, 15}:
        count = 10
    resume = session.get("resume_analysis")
    resume_data = resume.get("analysis", {}) if isinstance(resume, dict) else {}
    job_data = job["analyzed_data"]
    matching = match_resume_to_job(resume, {"success": True, "analysis": job_data}) if resume else {"success": False, "result": {}}
    matching_data = matching.get("result", {}) if matching.get("success") else {"missing_required_skills": job_data.get("required_skills", []), "missing_preferred_skills": job_data.get("preferred_skills", [])}
    try:
        weakness = detect_weak_topics(session["user_id"], app)
    except DatabaseError:
        flash("Previous performance is temporarily unavailable. We can still prepare from the job and resume.", "error")
        weakness = {"weak_topics": [], "has_data": False}
    plan = build_job_interview_plan(job_data, matching_data, weakness, difficulty, count)
    result = generate_interview_questions(resume_data or {"skills": []}, job_data, matching_data or {"job": job["title"]}, "mixed", difficulty, count, weak_topics=weakness.get("weak_topics", []))
    if not result.get("success"):
        flash(result.get("error", "Unable to generate this interview."), "error")
        return redirect(url_for("job_prep"))
    questions = [{"id": index + 1, **question} for index, question in enumerate(result["questions"])]
    session["generated_questions"] = questions
    session["generated_interview_config"] = {"interview_type": "job-specific", "difficulty": difficulty, "total_questions": count, "job_id": job["id"], "job_title": job["title"]}
    return render_template("job_plan.html", plan=plan, job=job)


@app.route("/resumes", methods=["GET"])
@login_required
def resumes():
    try:
        saved_resumes = get_user_resumes(session["user_id"], app)
        tailored = get_user_tailored_resumes(session["user_id"], app)
    except DatabaseError:
        flash("Your resume history is temporarily unavailable.", "error")
        saved_resumes, tailored = [], []
    return render_template("resumes.html", resumes=saved_resumes, tailored_resumes=tailored)


@app.route("/resume-tailor", methods=["GET", "POST"])
@login_required
@rate_limited
def resume_tailor_route():
    try:
        saved_resumes = get_user_resumes(session["user_id"], app)
        saved_jobs = get_user_jobs(session["user_id"], app)
    except DatabaseError:
        flash("Your resume and job history is temporarily unavailable.", "error")
        return redirect(url_for("home"))
    if request.method == "GET":
        return render_template("resume_tailor.html", resumes=saved_resumes, jobs=saved_jobs)
    try:
        resume = get_user_resume(request.form.get("resume_id", ""), session["user_id"], app)
        job = get_user_job(request.form.get("job_id", ""), session["user_id"], app)
    except (DatabaseError, ValueError):
        resume, job = None, None
    if not resume or not job or not resume.get("analyzed_data"):
        flash("Select an analyzed resume and a saved job first.", "error")
        return redirect(url_for("resume_tailor_route"))
    resume_data = resume["analyzed_data"]
    job_data = job["analyzed_data"]
    keywords = analyze_resume_keywords(resume_data, job_data)
    ats = calculate_ats_score(keywords, resume_data, job_data)
    analyzer = get_analyzer()
    if not analyzer:
        flash("AI service is not configured. Please set OPENAI_API_KEY.", "error")
        return redirect(url_for("resume_tailor_route"))
    result = tailor_resume(resume_data, job_data, keywords, analyzer.client, analyzer.model)
    if not result.get("success"):
        flash(result.get("error", "Unable to tailor the resume."), "error")
        return redirect(url_for("resume_tailor_route"))
    try:
        tailored_id = create_tailored_resume(session["user_id"], resume["id"], job["id"], json.dumps(result["tailored"]), ats["score"], app)
    except (DatabaseError, ValueError):
        flash("The tailored resume could not be saved.", "error")
        return redirect(url_for("resume_tailor_route"))
    return render_template("resume_tailor_preview.html", original=resume_data, tailored=result["tailored"], keywords=keywords, ats=ats, job=job, tailored_id=tailored_id)


@app.route("/resume-tailor/<tailored_id>", methods=["GET"])
@login_required
def tailored_resume_detail(tailored_id):
    try:
        tailored = get_user_tailored_resume(tailored_id, session["user_id"], app)
    except (DatabaseError, ValueError):
        tailored = None
    if not tailored:
        return render_template("interview_not_found.html"), 404
    try:
        tailored["content"] = json.loads(tailored["content"])
    except json.JSONDecodeError:
        return render_template("interview_not_found.html"), 404
    return render_template("resume_tailor_detail.html", tailored=tailored)


@app.route("/resume-tailor/<tailored_id>/download", methods=["GET"])
@login_required
def download_tailored_resume(tailored_id):
    try:
        tailored = get_user_tailored_resume(tailored_id, session["user_id"], app)
    except (DatabaseError, ValueError):
        tailored = None
    if not tailored:
        return render_template("interview_not_found.html"), 404
    try:
        content = json.loads(tailored["content"])
        pdf = resume_to_pdf(content)
    except (json.JSONDecodeError, TypeError):
        return render_template("interview_not_found.html"), 404
    return Response(pdf, mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=tailored-resume.pdf"})


@app.route("/job-prep/start", methods=["POST"])
@login_required
def start_job_interview():
    if not session.get("generated_questions") or session.get("generated_interview_config", {}).get("interview_type") != "job-specific":
        flash("Generate a job-specific interview plan first.", "error")
        return redirect(url_for("job_prep"))
    return redirect(url_for("start_interview"), code=307)


@app.route("/interview", methods=["GET"])
@login_required
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
        "voice_interview_session.html" if interview_state.get("interview_mode") == "voice" else "interview.html",
        question=interview_state["questions"][current_index],
        current_index=current_index,
        total_questions=len(interview_state["questions"]),
        answer=_answer_for_question(interview_state, interview_state["questions"][current_index]["id"]),
        error=None,
    )


@app.route("/submit-answer", methods=["POST"])
@login_required
@rate_limited
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
    answer_limit = 5000 if interview_state.get("interview_mode") == "voice" else MAX_ANSWER_LENGTH
    if len(answer) > answer_limit:
        return _render_interview_error(interview_state, f"Your answer is too long. Please keep it under {answer_limit:,} characters.", 400)
    if _answer_for_question(interview_state, current_question["id"]) is not None:
        return _render_interview_error(interview_state, "This answer was already submitted. Please continue with the current question.", 400)

    answer_record = {
        "question_id": current_question["id"],
        "question": current_question["question"],
        "answer": answer.strip(),
        "category": current_question["category"],
        "difficulty": current_question["difficulty"],
        "topic": current_question.get("topic", "Unspecified topic"),
    }
    if interview_state.get("interview_mode") == "voice":
        answer_record["voice_metrics"] = {
            "duration": request.form.get("voice_duration", type=int) or 0,
            "word_count": request.form.get("voice_word_count", type=int) or len(answer.strip().split()),
            "filler_count": request.form.get("voice_filler_count", type=int) or 0,
        }
    interview_state["answers"].append(answer_record)
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
@login_required
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
        performance = calculate_interview_performance(
            interview_state.get("answers", []),
            total_questions=len(interview_state["questions"]),
        )
        try:
            interview_id = save_completed_interview(interview_state, performance, session["user_id"], app, interview_state.get("job_id"))
            interview_state["database_id"] = interview_id
            session["completed_interview"] = interview_state
        except (DatabaseError, ValueError):
            flash("We could not save this interview, but your completed summary is still available.", "error")
            return redirect(url_for("finish_interview"))
        return redirect(url_for("finish_interview"))
    session["interview"] = interview_state
    return redirect(url_for("interview"))


@app.route("/finish-interview", methods=["GET"])
@login_required
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
        performance=calculate_interview_performance(completed["answers"], len(completed["questions"])),
        interview_mode=completed.get("interview_mode", "text"),
    )


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Render deterministic performance analytics for the completed interview."""
    completed = session.get("completed_interview")
    try:
        saved_interviews = get_user_interviews(session["user_id"], app)
    except DatabaseError:
        flash("Your interview data is temporarily unavailable.", "error")
        return redirect(url_for("home"))
    if _valid_interview_state(completed) and completed["current_index"] >= len(completed["questions"]):
        performance = calculate_interview_performance(completed.get("answers", []), len(completed["questions"]))
    elif saved_interviews:
        saved = get_user_interview(saved_interviews[0]["id"], session["user_id"], app)
        performance = _performance_for_saved_interview(saved)
    else:
        flash("Complete an interview to see your performance dashboard.", "error")
        return redirect(url_for("home"))
    stats = {
        "total_interviews": len(saved_interviews),
        "best_score": max((item["overall_score"] for item in saved_interviews if item["overall_score"] is not None), default=None),
        "average_score": round(sum(item["overall_score"] for item in saved_interviews if item["overall_score"] is not None) / max(1, sum(item["overall_score"] is not None for item in saved_interviews)), 1),
    }
    try:
        weakness_analysis = detect_weak_topics(session["user_id"], app)
    except DatabaseError:
        weakness_analysis = None
    return render_template("dashboard.html", performance=performance, user_stats=stats, weakness_analysis=weakness_analysis, readiness=_readiness_for_user(performance, saved_interviews))


def _readiness_for_user(performance, saved_interviews):
    try:
        roadmap_data = _current_roadmap()
        active_job = roadmap_data.get("job")
        return calculate_readiness(performance, roadmap_data, saved_interviews, active_job)
    except DatabaseError:
        return None


@app.route("/readiness", methods=["GET"])
@login_required
def readiness():
    try:
        saved_interviews = get_user_interviews(session["user_id"], app)
        if not saved_interviews:
            return render_template("readiness.html", report=None)
        latest = get_user_interview(saved_interviews[0]["id"], session["user_id"], app)
        performance = _performance_for_saved_interview(latest)
        report = _readiness_for_user(performance, saved_interviews)
        insight = None
        analyzer = get_analyzer()
        if analyzer and report:
            insight = explain_roadmap({"topics": [], "job": report.get("job")}, analyzer.client, analyzer.model)
        return render_template("readiness.html", report=report, insight=insight)
    except DatabaseError:
        flash("Your readiness report is temporarily unavailable.", "error")
        return redirect(url_for("home"))


def _current_roadmap():
    weakness = detect_weak_topics(session["user_id"], app)
    saved_jobs = get_user_jobs(session["user_id"], app)
    active_job = None
    if saved_jobs:
        active_job = get_user_job(saved_jobs[0]["id"], session["user_id"], app)
    return build_roadmap(weakness, saved_jobs, active_job)


@app.route("/roadmap", methods=["GET"])
@login_required
@rate_limited
def roadmap():
    try:
        result = _current_roadmap()
    except DatabaseError:
        flash("Your learning roadmap is temporarily unavailable.", "error")
        return redirect(url_for("home"))
    if not result["has_data"]:
        return render_template("roadmap.html", roadmap=result, no_data=True)
    explanation = None
    analyzer = get_analyzer()
    if analyzer:
        explanation = explain_roadmap(result, analyzer.client, analyzer.model)
    return render_template("roadmap.html", roadmap=result, no_data=False, explanation=explanation)


@app.route("/roadmap/topic/<topic>", methods=["GET"])
@login_required
def roadmap_topic(topic):
    try:
        result = _current_roadmap()
    except DatabaseError:
        return render_template("interview_not_found.html"), 404
    selected = next((item for item in result["topics"] if item["topic"].casefold() == topic.casefold()), None)
    if selected is None:
        return render_template("interview_not_found.html"), 404
    return render_template("topic_detail.html", topic=selected)


@app.route("/roadmap/today", methods=["GET"])
@login_required
def roadmap_today():
    try:
        result = _current_roadmap()
    except DatabaseError:
        return render_template("interview_not_found.html"), 404
    minutes = request.args.get("minutes", type=int) or 30
    return render_template("daily_plan.html", plan=build_daily_plan(result, minutes))


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Display all completed interviews stored in SQLite."""
    try:
        interviews = get_user_interviews(session["user_id"], app)
    except DatabaseError:
        flash("Interview history is temporarily unavailable.", "error")
        interviews = []
    return render_template("history.html", interviews=interviews)


@app.route("/history/<interview_id>", methods=["GET"])
@login_required
def interview_detail(interview_id):
    """Display one persisted interview and its submitted answers."""
    try:
        saved_interview = get_user_interview(interview_id, session["user_id"], app)
    except (DatabaseError, ValueError):
        saved_interview = None
    if saved_interview is None:
        return render_template("interview_not_found.html"), 404
    return render_template("interview_detail.html", interview=saved_interview)


@app.route("/history/<interview_id>/dashboard", methods=["GET"])
@login_required
def history_dashboard(interview_id):
    """Reuse the existing analytics function for a persisted interview."""
    try:
        saved_interview = get_user_interview(interview_id, session["user_id"], app)
    except (DatabaseError, ValueError):
        saved_interview = None
    if saved_interview is None:
        return render_template("interview_not_found.html"), 404
    performance = _performance_for_saved_interview(saved_interview)
    return render_template("dashboard.html", performance=performance, history_interview=saved_interview)


def _performance_for_saved_interview(saved_interview):
    answers = []
    for item in saved_interview["questions"]:
        evaluation = json.loads(item["evaluation_json"]) if item.get("evaluation_json") else None
        answer = {"category": item["category"], "topic": item["topic"], "answer": item.get("answer_text")}
        if evaluation:
            answer["evaluation"] = evaluation
        answers.append(answer)
    return calculate_interview_performance(answers, saved_interview["total_questions"])


@app.route("/history/<interview_id>/delete", methods=["POST"])
@login_required
def delete_history_interview(interview_id):
    """Delete a persisted interview using POST only."""
    try:
        deleted = delete_user_interview(interview_id, session["user_id"], app)
    except (DatabaseError, ValueError):
        deleted = False
    if not deleted:
        flash("Interview not found or could not be deleted.", "error")
    else:
        flash("Interview deleted.", "success")
    return redirect(url_for("history"))


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
        "voice_interview_session.html" if interview_state.get("interview_mode") == "voice" else "interview.html",
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
    app.run(debug=app.config["DEBUG"])
