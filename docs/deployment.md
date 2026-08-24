# Deployment

1. Create a production virtual environment and install `requirements.txt`.
2. Set `OPENAI_API_KEY`, a strong random `SECRET_KEY`, `DATABASE_PATH`, and `FLASK_DEBUG=False`.
3. Use a persistent database volume and back up SQLite; use PostgreSQL when concurrency requires it.
4. Run behind a production WSGI server and HTTPS reverse proxy.
5. Serve static files through the web server and use persistent storage for uploads.
6. Do not expose `.env`, database files, uploaded files, or debug stack traces.
7. Monitor application errors, AI failures, latency, rate limits, disk space, and database backups.

The built-in Flask server is for local development only.
