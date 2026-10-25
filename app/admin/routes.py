
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from slugify import slugify

from app.admin import admin_bp
from app.admin.forms import AdminLoginForm, CafeForm
from app.extensions import db
from app.models import Admin , Cafe , Area


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
    cafes = db.session.scalars(
        db.select(Cafe).order_by(Cafe.name)
    ).all()

    total_cafes = len(cafes)
    published_cafes = sum(cafe.published for cafe in cafes)
    draft_cafes = total_cafes - published_cafes

    return render_template(
        "admin/dashboard.html",
        cafes=cafes,
        total_cafes=total_cafes,
        published_cafes=published_cafes,
        draft_cafes=draft_cafes,
    )


@admin_bp.route("/cafes/new", methods=["GET", "POST"])
@login_required
def create_cafe():
    form = CafeForm()

    areas = db.session.scalars(
        db.select(Area).order_by(Area.name)
    ).all()

    # -1 is a special value meaning "create a new area".
    form.area_id.choices = [
        (area.id, area.name) for area in areas
    ] + [(-1, "+ Add new area...")]

    if form.validate_on_submit():
        name = form.name.data.strip()
        slug = slugify(name)

        if not slug:
            form.name.errors.append("Enter a valid cafe name.")
            return render_template(
                "admin/cafe_form.html",
                form=form,
                page_title="Add Cafe",
            )

        existing_cafe = db.session.scalar(
            db.select(Cafe).where(Cafe.slug == slug)
        )

        if existing_cafe:
            form.name.errors.append(
                "A cafe with this name already exists or generates a duplicate URL."
            )
            return render_template(
                "admin/cafe_form.html",
                form=form,
                page_title="Add Cafe",
            )

        # Resolve the selected area.
        if form.area_id.data == -1:
            area_name = (form.new_area_name.data or "").strip()

            if not area_name:
                form.new_area_name.errors.append(
                    "Enter a name for the new area."
                )
                return render_template(
                    "admin/cafe_form.html",
                    form=form,
                    page_title="Add Cafe",
                )

            area_slug = slugify(area_name)

            if not area_slug:
                form.new_area_name.errors.append(
                    "Enter a valid area name."
                )
                return render_template(
                    "admin/cafe_form.html",
                    form=form,
                    page_title="Add Cafe",
                )

            # Reuse an existing area if its slug already exists.
            area = db.session.scalar(
                db.select(Area).where(Area.slug == area_slug)
            )

            if area is None:
                area = Area(
                    name=area_name,
                    slug=area_slug,
                )
                db.session.add(area)
                db.session.flush()

        else:
            area = db.session.get(Area, form.area_id.data)

        if area is None:
            form.area_id.errors.append(
                "Please select a valid area."
            )
            return render_template(
                "admin/cafe_form.html",
                form=form,
                page_title="Add Cafe",
            )

        cafe = Cafe(
            name=name,
            slug=slug,
            address=form.address.data.strip(),
            description=form.description.data.strip(),
            area=area,
            price_level=form.price_level.data or None,
            wifi_available={
                "yes": True,
                "no": False,
                "unknown": None,
            }[form.wifi_available.data],
            power_outlets={
                "yes": True,
                "no": False,
                "unknown": None,
            }[form.power_outlets.data],
            published=False,
        )

        db.session.add(cafe)
        db.session.commit()

        flash(f"{cafe.name} was saved as a draft.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/cafe_form.html",
        form=form,
        page_title="Add Cafe",
    )


