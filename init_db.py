from app import app
from database.db import init_database


if __name__ == "__main__":
    init_database(app)
    print("Interview database is ready.")
