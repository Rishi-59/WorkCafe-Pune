
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.admin import admin_bp
from app.admin.forms import AdminLoginForm
from app.extensions import db
from app.models import Admin


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in? Go straight to the dashboard.
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()

        admin = db.session.scalar(
            db.select(Admin).where(Admin.username == username)
        )

        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash("Welcome back!", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    return render_template("admin/dashboard.html")
