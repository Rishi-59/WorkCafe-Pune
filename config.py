
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    database_url = os.environ.get("DATABASE_URL")

    if database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///workcafe.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Supabase Storage credentials
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")
    SUPABASE_BUCKET = "cafe-images"
