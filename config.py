"""Central application configuration."""

import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-secret")
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "instance", "interview_coach.db"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    MAX_ANSWER_LENGTH = 10000
    MAX_VOICE_TRANSCRIPT_LENGTH = 5000
    MAX_RECORDING_SECONDS = 180
    MAX_AI_REQUESTS_PER_MINUTE = int(os.getenv("MAX_AI_REQUESTS_PER_MINUTE", "20"))
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"


if not Config.SECRET_KEY and Config.DEBUG:
    Config.SECRET_KEY = "development-only-secret"
