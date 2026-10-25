
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = "sqlite:///workcafe.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
