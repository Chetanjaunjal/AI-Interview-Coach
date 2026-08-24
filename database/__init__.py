"""Persistence helpers for completed interview records."""

from .db import (
    DatabaseError,
    create_user,
    create_job,
    delete_user_interview,
    get_user_by_email,
    get_user_by_id,
    get_user_interview,
    get_user_interview_records,
    get_user_job,
    get_user_jobs,
    get_user_interviews,
    update_job_matching,
    init_database,
    save_completed_interview,
)

__all__ = [
    "DatabaseError",
    "create_user",
    "create_job",
    "delete_user_interview",
    "get_user_by_email",
    "get_user_by_id",
    "get_user_interview",
    "get_user_interview_records",
    "get_user_job",
    "get_user_jobs",
    "get_user_interviews",
    "update_job_matching",
    "init_database",
    "save_completed_interview",
]
