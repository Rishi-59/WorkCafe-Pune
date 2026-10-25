
from flask import render_template, abort
from sqlalchemy.orm import joinedload

from app.public import public_bp
from app.extensions import db
from app.models import Cafe, Area


@public_bp.route("/")
def home():
    cafes = db.session.scalars(
        db.select(Cafe)
        .options(joinedload(Cafe.area))
        .where(Cafe.published.is_(True))
        .order_by(Cafe.created_at.desc())
        .limit(3)
    ).all()

    return render_template("public/home.html", cafes=cafes)


@public_bp.route("/cafes")
def cafes():
    cafe_list = db.session.scalars(
        db.select(Cafe)
        .options(joinedload(Cafe.area))
        .where(Cafe.published.is_(True))
        .order_by(Cafe.name)
    ).all()

    return render_template("public/cafes.html", cafes=cafe_list)


@public_bp.route("/cafes/<slug>")
def cafe_detail(slug):
    cafe = db.session.scalar(
        db.select(Cafe)
        .options(joinedload(Cafe.area))
        .where(
            Cafe.slug == slug,
            Cafe.published.is_(True),
        )
    )

    if cafe is None:
        abort(404)

    return render_template("public/cafe_detail.html", cafe=cafe)


@public_bp.route("/areas/<area_slug>")
def area_detail(area_slug):
    area = db.session.scalar(
        db.select(Area).where(Area.slug == area_slug)
    )

    if area is None:
        abort(404)

    cafes = db.session.scalars(
        db.select(Cafe)
        .where(
            Cafe.area_id == area.id,
            Cafe.published.is_(True),
        )
        .order_by(Cafe.name)
    ).all()

    return render_template(
        "public/area.html",
        area=area,
        cafes=cafes,
    )


@public_bp.route("/about")
def about():
    return render_template("public/about.html")
