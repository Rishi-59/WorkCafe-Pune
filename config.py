
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///workcafe.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR, "app", "static", "uploads"
    )
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
