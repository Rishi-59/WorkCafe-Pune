
import os

from flask import Flask, redirect, url_for, flash, request
from config import Config
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)

    # Load application settings
    app.config.from_object(config_class)

    # Ensure the instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "warning"

    # Import models so SQLAlchemy registers the tables
    from app import models

    # Load an admin from their ID stored in the session
    @login_manager.user_loader
    def load_user(user_id):
        if not user_id.isdigit():
            return None

        return db.session.get(models.Admin, int(user_id))

    # Register blueprints
    from app.public import public_bp
    from app.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.errorhandler(413)
    def request_entity_too_large(error):
        flash(
            "The uploaded file is too large. Maximum request size is 5 MB.",
            "danger",
        )
        return redirect(request.referrer or url_for("admin.dashboard"))

    return app
