
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    SelectField,
    BooleanField,
)
from wtforms.validators import DataRequired, Length, Optional

class CafeForm(FlaskForm):
    name = StringField(
        "Cafe Name",
        validators=[DataRequired(), Length(max=150)],
    )

    address = StringField(
        "Address",
        validators=[DataRequired(), Length(max=255)],
    )

    description = TextAreaField(
        "Description",
        validators=[DataRequired()],
    )

    area_id = SelectField(
        "Area",
        coerce=int,
        validators=[DataRequired()],
    )

    new_area_name = StringField(
        "New Area Name",
        validators=[Optional(), Length(max=100)],
    )

    image = FileField(
        "Cafe Image",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp"],
                "Only JPG, PNG, and WEBP images are allowed.",
            ),
        ],
    )

    price_level = SelectField(
        "Price Level",
        choices=[
            ("", "Select price level"),
            ("Budget", "Budget"),
            ("Moderate", "Moderate"),
            ("Premium", "Premium"),
        ],
        validators=[Optional()],
    )

    wifi_available = SelectField(
        "Wi-Fi Availability",
        choices=[
            ("unknown", "Not verified"),
            ("yes", "Available"),
            ("no", "Unavailable"),
        ],
        default="unknown",
        validators=[DataRequired()],
    )

    power_outlets = SelectField(
        "Power Outlets",
        choices=[
            ("unknown", "Not verified"),
            ("yes", "Available"),
            ("no", "Unavailable"),
        ],
        default="unknown",
        validators=[DataRequired()],
    )

    submit = SubmitField("Save as Draft")


class AdminLoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired()],
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()],
    )

    submit = SubmitField("Log in")
