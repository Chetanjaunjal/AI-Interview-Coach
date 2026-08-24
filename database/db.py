"""Small SQLite data layer for persistent completed interviews."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any
from werkzeug.security import generate_password_hash


class DatabaseError(Exception):
    """Raised when a database operation cannot be completed safely."""


def database_path(app=None):
    if app is not None:
        configured_path = app.config.get("DATABASE_PATH")
        if configured_path:
            return configured_path
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "interview_coach.db")


def get_db_connection(app=None):
    path = database_path(app)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database(app=None):
    try:
        with get_db_connection(app) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS interviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interview_type TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    total_questions INTEGER NOT NULL CHECK (total_questions > 0),
                    overall_score REAL CHECK (overall_score IS NULL OR overall_score BETWEEN 0 AND 10),
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    user_id INTEGER,
                    job_id INTEGER,
                    interview_mode TEXT NOT NULL DEFAULT 'text',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interview_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    question_order INTEGER NOT NULL,
                    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL UNIQUE,
                    answer_text TEXT NOT NULL,
                    relevance_score REAL CHECK (relevance_score IS NULL OR relevance_score BETWEEN 0 AND 10),
                    correctness_score REAL CHECK (correctness_score IS NULL OR correctness_score BETWEEN 0 AND 10),
                    completeness_score REAL CHECK (completeness_score IS NULL OR completeness_score BETWEEN 0 AND 10),
                    communication_score REAL CHECK (communication_score IS NULL OR communication_score BETWEEN 0 AND 10),
                    overall_score REAL CHECK (overall_score IS NULL OR overall_score BETWEEN 0 AND 10),
                    feedback TEXT,
                    evaluation_json TEXT,
                    voice_metrics_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_questions_interview_id ON questions(interview_id);
                CREATE INDEX IF NOT EXISTS idx_interviews_completed_at ON interviews(completed_at);
                """
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    original_filename TEXT,
                    extracted_text TEXT NOT NULL,
                    analyzed_data TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS tailored_resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    resume_id INTEGER NOT NULL,
                    job_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    ats_score REAL NOT NULL CHECK (ats_score BETWEEN 0 AND 100),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(interviews)")}
            if "user_id" not in columns:
                connection.execute("ALTER TABLE interviews ADD COLUMN user_id INTEGER")
            if "job_id" not in columns:
                connection.execute("ALTER TABLE interviews ADD COLUMN job_id INTEGER")
            if "interview_mode" not in columns:
                connection.execute("ALTER TABLE interviews ADD COLUMN interview_mode TEXT NOT NULL DEFAULT 'text'")
            answer_columns = {row[1] for row in connection.execute("PRAGMA table_info(answers)")}
            if "voice_metrics_json" not in answer_columns:
                connection.execute("ALTER TABLE answers ADD COLUMN voice_metrics_json TEXT")
            legacy = connection.execute("SELECT id FROM users WHERE email = ?", ("legacy@local.invalid",)).fetchone()
            if legacy is None:
                cursor = connection.execute(
                    "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    ("Legacy Interviews", "legacy@local.invalid", generate_password_hash(os.urandom(32).hex(), method="pbkdf2:sha256"), _now()),
                )
                legacy_id = cursor.lastrowid
            else:
                legacy_id = legacy[0]
            connection.execute("UPDATE interviews SET user_id = ? WHERE user_id IS NULL", (legacy_id,))
            connection.execute("CREATE INDEX IF NOT EXISTS idx_interviews_user_id ON interviews(user_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_interviews_job_id ON interviews(job_id)")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    company_name TEXT,
                    description TEXT NOT NULL,
                    analyzed_data TEXT NOT NULL,
                    matching_data TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )"""
            )
    except sqlite3.Error as error:
        raise DatabaseError("Unable to initialize the interview database.") from error


def _require_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _score(value: Any, field: str, required=False):
    if value is None or value == "":
        if required:
            raise ValueError(f"{field} is required")
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be between 0 and 10")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be between 0 and 10") from error
    if not 0 <= numeric_value <= 10:
        raise ValueError(f"{field} must be between 0 and 10")
    return numeric_value


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_user(name, email, password_hash, app=None):
    name = _require_text(name, "name")
    email = _require_text(email, "email").lower()
    password_hash = _require_text(password_hash, "password_hash")
    try:
        with get_db_connection(app) as connection:
            cursor = connection.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, _now()),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as error:
        raise ValueError("An account with this email already exists.") from error
    except sqlite3.Error as error:
        raise DatabaseError("Unable to create the account.") from error


def get_user_by_email(email, app=None):
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?", (str(email or "").strip().lower(),)).fetchone()
            return dict(row) if row else None
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load the account.") from error


def get_user_by_id(user_id, app=None):
    value = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (value,)).fetchone()
            return dict(row) if row else None
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load the account.") from error


def save_completed_interview(completed, performance, user_id=None, app=None, job_id=None):
    if not isinstance(completed, dict) or not isinstance(performance, dict):
        raise ValueError("Invalid completed interview data")
    questions = completed.get("questions")
    answers = completed.get("answers")
    if not isinstance(questions, list) or not questions or not isinstance(answers, list):
        raise ValueError("An interview must include questions and answers")
    interview_type = _require_text(completed.get("interview_type"), "interview_type")
    difficulty = _require_text(completed.get("difficulty"), "difficulty")
    if app is None and hasattr(user_id, "config"):
        app = user_id
        legacy_user = get_user_by_email("legacy@local.invalid", app)
        user_id = legacy_user["id"] if legacy_user else None
    user_id = _valid_id(user_id)
    if job_id is not None:
        job_id = _valid_id(job_id)
    started_at = completed.get("started_at") or _now()
    completed_at = _now()
    overall_score = _score(performance.get("overall_score"), "overall_score")
    answer_by_question = {item.get("question_id"): item for item in answers if isinstance(item, dict)}

    try:
        with get_db_connection(app) as connection:
            cursor = connection.execute(
                "INSERT INTO interviews (interview_type, difficulty, total_questions, overall_score, started_at, completed_at, user_id, job_id, interview_mode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (interview_type, difficulty, len(questions), overall_score, started_at, completed_at, user_id, job_id, completed.get("interview_mode", "text")),
            )
            interview_id = cursor.lastrowid
            for order, question in enumerate(questions, start=1):
                question_text = _require_text(question.get("question"), "question text")
                cursor = connection.execute(
                    "INSERT INTO questions (interview_id, question_text, category, difficulty, topic, question_order) VALUES (?, ?, ?, ?, ?, ?)",
                    (interview_id, question_text, _require_text(question.get("category"), "category"), _require_text(question.get("difficulty"), "difficulty"), _require_text(question.get("topic", "Unspecified topic"), "topic"), order),
                )
                answer = answer_by_question.get(question.get("id"))
                if not isinstance(answer, dict):
                    raise ValueError("Every question must have an answer")
                answer_text = _require_text(answer.get("answer"), "answer text")
                evaluation = answer.get("evaluation") if isinstance(answer.get("evaluation"), dict) else {}
                correctness_key = "technical_correctness" if "technical_correctness" in evaluation else "content_quality"
                scores = (
                    _score(evaluation.get("relevance"), "relevance_score"),
                    _score(evaluation.get(correctness_key), "correctness_score"),
                    _score(evaluation.get("completeness"), "completeness_score"),
                    _score(evaluation.get("communication"), "communication_score"),
                    _score(evaluation.get("overall_score"), "overall_score"),
                )
                feedback = evaluation.get("model_feedback") or answer.get("evaluation_error")
                connection.execute(
                    "INSERT INTO answers (question_id, answer_text, relevance_score, correctness_score, completeness_score, communication_score, overall_score, feedback, evaluation_json, voice_metrics_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (cursor.lastrowid, answer_text, *scores, str(feedback) if feedback else None, json.dumps(evaluation) if evaluation else None, json.dumps(answer.get("voice_metrics")) if isinstance(answer.get("voice_metrics"), dict) else None, _now()),
                )
            return interview_id
    except (sqlite3.Error, ValueError, TypeError, json.JSONDecodeError) as error:
        if isinstance(error, ValueError):
            raise
        raise DatabaseError("Unable to save the completed interview.") from error


def get_all_interviews(app=None):
    try:
        with get_db_connection(app) as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM interviews ORDER BY completed_at DESC, id DESC")]
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load interview history.") from error


def get_user_interviews(user_id, app=None):
    value = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            return [dict(row) for row in connection.execute("SELECT i.*, j.title AS job_title FROM interviews i LEFT JOIN jobs j ON j.id = i.job_id WHERE i.user_id = ? ORDER BY i.completed_at DESC, i.id DESC", (value,))]
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load interview history.") from error


def get_user_interview_records(user_id, app=None):
    """Return evaluated answer records joined to only one user's interviews."""
    value = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            rows = connection.execute(
                """SELECT i.id AS interview_id, i.completed_at, i.interview_type, i.job_id, q.id AS question_id,
                          q.topic, q.category, a.id AS answer_id,
                          a.relevance_score, a.correctness_score, a.completeness_score,
                          a.communication_score, a.overall_score, a.evaluation_json
                   FROM interviews i
                   JOIN questions q ON q.interview_id = i.id
                   LEFT JOIN answers a ON a.question_id = q.id
                   WHERE i.user_id = ?
                   ORDER BY i.completed_at DESC, i.id DESC, q.question_order""",
                (value,),
            )
            records = []
            for row in rows:
                record = dict(row)
                evaluation = json.loads(record.pop("evaluation_json")) if record.get("evaluation_json") else {}
                record["missing_concepts"] = evaluation.get("missing_points", []) if isinstance(evaluation, dict) else []
                records.append(record)
            return records
    except (sqlite3.Error, json.JSONDecodeError) as error:
        raise DatabaseError("Unable to load performance data.") from error


def _valid_id(interview_id):
    try:
        value = int(interview_id)
    except (TypeError, ValueError) as error:
        raise ValueError("Interview ID must be an integer") from error
    if value < 1:
        raise ValueError("Interview ID must be positive")
    return value


def create_job(user_id, title, company_name, description, analyzed_data, app=None):
    user_id = _valid_id(user_id)
    title = _require_text(title, "job title")
    description = _require_text(description, "job description")
    if not isinstance(analyzed_data, dict):
        raise ValueError("Invalid job analysis")
    try:
        with get_db_connection(app) as connection:
            cursor = connection.execute(
                "INSERT INTO jobs (user_id, title, company_name, description, analyzed_data, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, title, str(company_name or "").strip() or None, description, json.dumps(analyzed_data), _now()),
            )
            return cursor.lastrowid
    except sqlite3.Error as error:
        raise DatabaseError("Unable to save the job.") from error


def create_resume(user_id, original_filename, extracted_text, analyzed_data=None, app=None):
    user_id = _valid_id(user_id)
    text = _require_text(extracted_text, "resume text")
    try:
        with get_db_connection(app) as connection:
            cursor = connection.execute("INSERT INTO resumes (user_id, original_filename, extracted_text, analyzed_data, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, str(original_filename or "").strip() or None, text, json.dumps(analyzed_data) if isinstance(analyzed_data, dict) else None, _now()))
            return cursor.lastrowid
    except sqlite3.Error as error:
        raise DatabaseError("Unable to save the resume.") from error


def update_resume_analysis(resume_id, user_id, analyzed_data, app=None):
    resume_id = _valid_id(resume_id)
    user_id = _valid_id(user_id)
    if not isinstance(analyzed_data, dict):
        raise ValueError("Invalid resume analysis")
    try:
        with get_db_connection(app) as connection:
            connection.execute("UPDATE resumes SET analyzed_data = ? WHERE id = ? AND user_id = ?", (json.dumps(analyzed_data), resume_id, user_id))
    except sqlite3.Error as error:
        raise DatabaseError("Unable to save resume analysis.") from error


def get_user_resumes(user_id, app=None):
    user_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            return [dict(row) for row in connection.execute("SELECT id, user_id, original_filename, created_at, analyzed_data IS NOT NULL AS analyzed FROM resumes WHERE user_id = ? ORDER BY created_at DESC, id DESC", (user_id,))]
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load resumes.") from error


def get_user_resume(resume_id, user_id, app=None):
    resume_id = _valid_id(resume_id)
    user_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT * FROM resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)).fetchone()
            if not row:
                return None
            resume = dict(row)
            resume["analyzed_data"] = json.loads(resume["analyzed_data"]) if resume.get("analyzed_data") else {}
            return resume
    except (sqlite3.Error, json.JSONDecodeError) as error:
        raise DatabaseError("Unable to load the resume.") from error


def create_tailored_resume(user_id, resume_id, job_id, content, ats_score, app=None):
    user_id = _valid_id(user_id)
    resume_id = _valid_id(resume_id)
    job_id = _valid_id(job_id)
    content = _require_text(content, "tailored resume content")
    try:
        score = float(ats_score)
    except (TypeError, ValueError) as error:
        raise ValueError("ats_score must be between 0 and 100") from error
    if not 0 <= score <= 100:
        raise ValueError("ats_score must be between 0 and 100")
    try:
        with get_db_connection(app) as connection:
            cursor = connection.execute("INSERT INTO tailored_resumes (user_id, resume_id, job_id, content, ats_score, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, resume_id, job_id, content, score, _now()))
            return cursor.lastrowid
    except sqlite3.Error as error:
        raise DatabaseError("Unable to save the tailored resume.") from error


def get_user_tailored_resumes(user_id, app=None):
    user_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            return [dict(row) for row in connection.execute("SELECT t.*, r.original_filename, j.title AS job_title FROM tailored_resumes t JOIN resumes r ON r.id = t.resume_id JOIN jobs j ON j.id = t.job_id WHERE t.user_id = ? ORDER BY t.created_at DESC, t.id DESC", (user_id,))]
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load tailored resumes.") from error


def get_user_tailored_resume(tailored_id, user_id, app=None):
    tailored_id = _valid_id(tailored_id)
    user_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT t.*, r.original_filename, j.title AS job_title FROM tailored_resumes t JOIN resumes r ON r.id = t.resume_id JOIN jobs j ON j.id = t.job_id WHERE t.id = ? AND t.user_id = ?", (tailored_id, user_id)).fetchone()
            return dict(row) if row else None
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load the tailored resume.") from error


def get_user_jobs(user_id, app=None):
    user_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            return [dict(row) for row in connection.execute("SELECT j.*, COUNT(i.id) AS interview_count FROM jobs j LEFT JOIN interviews i ON i.job_id = j.id WHERE j.user_id = ? GROUP BY j.id ORDER BY j.created_at DESC, j.id DESC", (user_id,))]
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load jobs.") from error


def get_user_job(job_id, user_id, app=None):
    job_id = _valid_id(job_id)
    user_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ? AND user_id = ?", (job_id, user_id)).fetchone()
            if not row:
                return None
            job = dict(row)
            job["analyzed_data"] = json.loads(job["analyzed_data"])
            job["matching_data"] = json.loads(job["matching_data"]) if job.get("matching_data") else {}
            return job
    except (sqlite3.Error, json.JSONDecodeError) as error:
        raise DatabaseError("Unable to load the job.") from error


def update_job_matching(job_id, user_id, matching_data, app=None):
    job_id = _valid_id(job_id)
    user_id = _valid_id(user_id)
    if not isinstance(matching_data, dict):
        raise ValueError("Invalid matching data")
    try:
        with get_db_connection(app) as connection:
            connection.execute("UPDATE jobs SET matching_data = ? WHERE id = ? AND user_id = ?", (json.dumps(matching_data), job_id, user_id))
    except sqlite3.Error as error:
        raise DatabaseError("Unable to save matching data.") from error


def get_user_interview(interview_id, user_id, app=None):
    value = _valid_id(interview_id)
    owner_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT i.*, j.title AS job_title FROM interviews i LEFT JOIN jobs j ON j.id = i.job_id WHERE i.id = ? AND i.user_id = ?", (value, owner_id)).fetchone()
            if row is None:
                return None
            interview = dict(row)
            interview["questions"] = [dict(item) for item in connection.execute("SELECT q.*, a.* FROM questions q LEFT JOIN answers a ON a.question_id = q.id WHERE q.interview_id = ? ORDER BY q.question_order", (value,))]
            for question in interview["questions"]:
                question["voice_metrics"] = json.loads(question["voice_metrics_json"]) if question.get("voice_metrics_json") else None
            return interview
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load the interview.") from error


def get_interview(interview_id, app=None):
    """Compatibility helper retained for non-authenticated migration tooling."""
    value = _valid_id(interview_id)
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT * FROM interviews WHERE id = ?", (value,)).fetchone()
            if row is None:
                return None
            interview = dict(row)
            interview["questions"] = [dict(item) for item in connection.execute("SELECT q.*, a.* FROM questions q LEFT JOIN answers a ON a.question_id = q.id WHERE q.interview_id = ? ORDER BY q.question_order", (value,))]
            for question in interview["questions"]:
                question["voice_metrics"] = json.loads(question["voice_metrics_json"]) if question.get("voice_metrics_json") else None
            return interview
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load the interview.") from error


def get_interview_questions(interview_id, app=None):
    interview = get_interview(interview_id, app)
    return interview.get("questions", []) if interview else []


def get_question_answers(question_id, app=None):
    value = _valid_id(question_id)
    try:
        with get_db_connection(app) as connection:
            row = connection.execute("SELECT * FROM answers WHERE question_id = ?", (value,)).fetchone()
            return dict(row) if row else None
    except sqlite3.Error as error:
        raise DatabaseError("Unable to load the answer.") from error


def delete_user_interview(interview_id, user_id, app=None):
    value = _valid_id(interview_id)
    owner_id = _valid_id(user_id)
    try:
        with get_db_connection(app) as connection:
            cursor = connection.execute("DELETE FROM interviews WHERE id = ? AND user_id = ?", (value, owner_id))
            return cursor.rowcount == 1
    except sqlite3.Error as error:
        raise DatabaseError("Unable to delete the interview.") from error


def delete_interview(interview_id, app=None):
    """Compatibility helper retained for old local database tooling."""
    value = _valid_id(interview_id)
    try:
        with get_db_connection(app) as connection:
            cursor = connection.execute("DELETE FROM interviews WHERE id = ?", (value,))
            return cursor.rowcount == 1
    except sqlite3.Error as error:
        raise DatabaseError("Unable to delete the interview.") from error
