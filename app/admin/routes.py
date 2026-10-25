import os
from uuid import uuid4

from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from slugify import slugify
from sqlalchemy.exc import SQLAlchemyError

from app.admin import admin_bp
from app.admin.forms import AdminLoginForm, CafeForm
from app.extensions import db
from app.models import Admin, Cafe, Area

from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

import logging
from urllib.parse import unquote, urlparse

from supabase import create_client

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_supabase_storage():
    """Return the configured Supabase Storage bucket."""
    supabase_url = current_app.config.get("SUPABASE_URL")
    secret_key = current_app.config.get("SUPABASE_SECRET_KEY")
    bucket_name = current_app.config.get("SUPABASE_BUCKET")

    if not supabase_url or not secret_key or not bucket_name:
        raise RuntimeError("Supabase Storage configuration is missing.")

    client = create_client(supabase_url, secret_key)
    return client.storage.from_(bucket_name)


def save_cafe_image(upload):
    """Validate an uploaded image and store it in Supabase Storage."""
    if not upload or not upload.filename:
        return None

    safe_name = secure_filename(upload.filename)
    extension = os.path.splitext(safe_name)[1].lower()

    if not safe_name or extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported file type. Use JPG, PNG, or WEBP.")

    try:
        upload.stream.seek(0)

        with Image.open(upload.stream) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError(
                    "The uploaded file must be a JPG, PNG, or WEBP image."
                )
            image.verify()

        upload.stream.seek(0)
        image_bytes = upload.stream.read()

    except ValueError:
        raise
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError("The uploaded file is not a valid image.") from error

    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    filename = f"{uuid4().hex}{extension}"

    try:
        storage = get_supabase_storage()

        storage.upload(
            filename,
            image_bytes,
            file_options={
                "content-type": content_types[extension],
                "upsert": "false",
            },
        )

        return storage.get_public_url(filename)

    except Exception as error:
        current_app.logger.exception("Supabase image upload failed.")
        raise ValueError(
            "The image could not be uploaded. Please try again."
        ) from error


def delete_cafe_image(image_url):
    """Delete an image from Supabase Storage using its public URL."""
    if not image_url:
        return

    bucket_name = current_app.config.get("SUPABASE_BUCKET")
    parsed_url = urlparse(image_url)

    expected_prefix = (
        f"/storage/v1/object/public/{bucket_name}/"
    )

    if not bucket_name or not parsed_url.path.startswith(expected_prefix):
        # Ignore old local filenames or URLs that aren't from this bucket.
        return

    object_path = unquote(parsed_url.path[len(expected_prefix):])

    if not object_path:
        return

    try:
        storage = get_supabase_storage()
        storage.remove([object_path])
    except Exception:
        # Don't make a successful database update appear to have failed
        # just because an old image couldn't be deleted.
        current_app.logger.exception(
            "Could not delete image from Supabase Storage."
        )


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

        try:
            image_filename = save_cafe_image(form.image.data)
        except ValueError as error:
            flash(str(error), "danger")
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
                "yes": True, "no": False, "unknown": None
            }[form.wifi_available.data],
            power_outlets={
                "yes": True, "no": False, "unknown": None
            }[form.power_outlets.data],
            image_filename=image_filename,
            published=False,
        )

        db.session.add(cafe)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()

            # Remove the uploaded image if the database save failed.
            if image_filename:
                delete_cafe_image(image_filename)

            current_app.logger.exception("Could not create cafe.")
            flash("Could not save the cafe. Please try again.", "danger")

            return render_template(
                "admin/cafe_form.html",
                form=form,
                page_title="Add Cafe",
            )

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

    # Populate fields only on the initial GET request.
    if not form.is_submitted():
        form.name.data = cafe.name
        form.address.data = cafe.address
        form.description.data = cafe.description
        form.area_id.data = cafe.area_id
        form.price_level.data = cafe.price_level or ""

        form.wifi_available.data = (
            "unknown"
            if cafe.wifi_available is None
            else "yes" if cafe.wifi_available else "no"
        )

        form.power_outlets.data = (
            "unknown"
            if cafe.power_outlets is None
            else "yes" if cafe.power_outlets else "no"
        )

    if form.validate_on_submit():
        name = form.name.data.strip()
        slug = slugify(name)

        if not slug:
            form.name.errors.append("Enter a valid cafe name.")
            return render_template(
                "admin/cafe_form.html",
                form=form,
                cafe=cafe,
                page_title="Edit Cafe",
            )

        # Prevent another cafe from using the same slug.
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
                cafe=cafe,
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
                    cafe=cafe,
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
                    cafe=cafe,
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
            db.session.rollback()
            form.area_id.errors.append("Select a valid area.")
            return render_template(
                "admin/cafe_form.html",
                form=form,
                cafe=cafe,
                page_title="Edit Cafe",
            )

        # Save a replacement image before changing the cafe record.
        old_image_filename = cafe.image_filename
        new_image_filename = None

        if form.image.data and form.image.data.filename:
            try:
                new_image_filename = save_cafe_image(form.image.data)
            except ValueError as error:
                db.session.rollback()
                flash(str(error), "danger")

                return render_template(
                    "admin/cafe_form.html",
                    form=form,
                    cafe=cafe,
                    page_title="Edit Cafe",
                )

        # Update the cafe fields.
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

        if new_image_filename:
            cafe.image_filename = new_image_filename

        # Commit the database changes.
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()

            # Avoid leaving the newly uploaded image orphaned.
            if new_image_filename:
                delete_cafe_image(new_image_filename)

            flash(
                "Could not update the cafe. Please try again.",
                "danger",
            )
            return render_template(
                "admin/cafe_form.html",
                form=form,
                cafe=cafe,
                page_title="Edit Cafe",
            )

        # Delete the old image only after the commit succeeds.
        if new_image_filename and old_image_filename:
            try:
                delete_cafe_image(old_image_filename)
            except OSError:
                # The database update succeeded; don't undo it
                # just because cleanup of the old file failed.
                current_app.logger.exception(
                    "Could not delete the previous cafe image."
                )

        flash(
            f"{cafe.name} was updated successfully.",
            "success",
        )
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/cafe_form.html",
        form=form,
        cafe=cafe,
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
