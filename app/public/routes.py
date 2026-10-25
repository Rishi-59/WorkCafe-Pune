
from flask import render_template

from app.public import public_bp

@public_bp.route("/")
def home():
    return render_template("public/home.html")
