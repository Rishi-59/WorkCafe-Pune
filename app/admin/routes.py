import os
from uuid import uuid4

from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from slugify import slugify

from app.admin import admin_bp
from app.admin.forms import AdminLoginForm, CafeForm
from app.extensions import db
from app.models import Admin, Cafe, Area

from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}



def save_cafe_image(upload):
    """Validate and save an uploaded image."""

    if not upload or not upload.filename:
        return None

    safe_name = secure_filename(upload.filename)
    extension = os.path.splitext(safe_name)[1].lower()

    if not safe_name or extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Use JPG, PNG, or WEBP."
        )

    # Validate the actual file contents, not just its extension.
    try:
        upload.stream.seek(0)

        with Image.open(upload.stream) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError(
                    "The uploaded file must be a JPG, PNG, or WEBP image."
                )

            image.verify()

        upload.stream.seek(0)

    except (UnidentifiedImageError, OSError) as error:
        raise ValueError(
            "The uploaded file is not a valid image."
        ) from error

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"{uuid4().hex}{extension}"
    filepath = os.path.join(upload_folder, filename)

    try:
        upload.save(filepath)
    except OSError as error:
        raise ValueError(
            "The image could not be saved. Please try again."
        ) from error

    return filename


def delete_cafe_image(filename):
    """Delete an old uploaded image if it exists."""
    if not filename:
        return

    upload_folder = os.path.abspath(
        current_app.config["UPLOAD_FOLDER"]
    )
    filepath = os.path.abspath(
        os.path.join(upload_folder, filename)
    )

    # Ensure the file is inside the configured upload folder.
    if os.path.commonpath([upload_folder, filepath]) != upload_folder:
        return

    if os.path.isfile(filepath):
        os.remove(filepath)


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

        image_filename = save_cafe_image(form.image.data)

        cafe = Cafe(
            name=name,
            slug=slug,
            address=form.address.data.strip(),
            description=form.description.data.strip(),
            area=area,
            price_level=form.price_level.data or None,
            wifi_available={
                "yes": True, "no": False, "unknown": None
            }[form.wifi_available.data],
            power_outlets={
                "yes": True, "no": False, "unknown": None
            }[form.power_outlets.data],
            image_filename=image_filename,
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


@admin_bp.route("/cafes/<int:cafe_id>/edit", methods=["GET", "POST"])
@login_required
def edit_cafe(cafe_id):
    cafe = db.get_or_404(Cafe, cafe_id)
    form = CafeForm()

    # Populate the dropdown with existing areas.
    areas = db.session.scalars(
        db.select(Area).order_by(Area.name)
    ).all()

    form.area_id.choices = [
                               (area.id, area.name) for area in areas
                           ] + [(-1, "+ Add new area...")]

    # Fill the form with existing cafe data on the first visit.
    if not form.is_submitted():
        form.name.data = cafe.name
        form.address.data = cafe.address
        form.description.data = cafe.description
        form.area_id.data = cafe.area_id
        form.price_level.data = cafe.price_level or ""
        form.wifi_available.data = (
            "unknown" if cafe.wifi_available is None
            else "yes" if cafe.wifi_available
            else "no"
        )
        form.power_outlets.data = (
            "unknown" if cafe.power_outlets is None
            else "yes" if cafe.power_outlets
            else "no"
        )

    if form.validate_on_submit():
        name = form.name.data.strip()
        slug = slugify(name)

        if not slug:
            form.name.errors.append("Enter a valid cafe name.")
            return render_template(
                "admin/cafe_form.html",
                form=form,
                page_title="Edit Cafe",
            )

        # Allow the cafe to keep its own slug, but reject another
        # cafe with the same generated slug.
        existing_cafe = db.session.scalar(
            db.select(Cafe).where(
                Cafe.slug == slug,
                Cafe.id != cafe.id,
            )
        )

        if existing_cafe:
            form.name.errors.append(
                "Another cafe already uses this name or URL slug."
            )
            return render_template(
                "admin/cafe_form.html",
                form=form,
                page_title="Edit Cafe",
            )

        # Resolve the selected area or create a new one.
        if form.area_id.data == -1:
            area_name = (form.new_area_name.data or "").strip()

            if not area_name:
                form.new_area_name.errors.append(
                    "Enter a name for the new area."
                )
                return render_template(
                    "admin/cafe_form.html",
                    form=form,
                    page_title="Edit Cafe",
                )

            area_slug = slugify(area_name)

            if not area_slug:
                form.new_area_name.errors.append(
                    "Enter a valid area name."
                )
                return render_template(
                    "admin/cafe_form.html",
                    form=form,
                    page_title="Edit Cafe",
                )

            area = db.session.scalar(
                db.select(Area).where(Area.slug == area_slug)
            )

            if area is None:
                area = Area(name=area_name, slug=area_slug)
                db.session.add(area)
                db.session.flush()
        else:
            area = db.session.get(Area, form.area_id.data)

        if area is None:
            form.area_id.errors.append("Select a valid area.")
            return render_template(
                "admin/cafe_form.html",
                form=form,
                page_title="Edit Cafe",
            )

        # Update the existing database object.
        cafe.name = name
        cafe.slug = slug
        cafe.address = form.address.data.strip()
        cafe.description = form.description.data.strip()
        cafe.area = area
        cafe.price_level = form.price_level.data or None
        cafe.wifi_available = {
            "yes": True,
            "no": False,
            "unknown": None,
        }[form.wifi_available.data]
        cafe.power_outlets = {
            "yes": True,
            "no": False,
            "unknown": None,
        }[form.power_outlets.data]

        old_image_filename = cafe.image_filename
        new_image_filename = None

        if form.image.data and form.image.data.filename:
            new_image_filename = save_cafe_image(form.image.data)
            cafe.image_filename = new_image_filename

        db.session.commit()

        # Remove the previous image only after the database update succeeds.
        if new_image_filename and old_image_filename:
            delete_cafe_image(old_image_filename)


        flash(f"{cafe.name} was updated successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/cafe_form.html",
        form=form,
        page_title="Edit Cafe",
    )


@admin_bp.route(
    "/cafes/<int:cafe_id>/toggle-publish",
    methods=["POST"],
)
@login_required
def toggle_publish(cafe_id):
    cafe = db.get_or_404(Cafe, cafe_id)

    cafe.published = not cafe.published
    db.session.commit()

    if cafe.published:
        flash(f"{cafe.name} is now published.", "success")
    else:
        flash(f"{cafe.name} has been unpublished.", "info")

    return redirect(url_for("admin.dashboard"))
