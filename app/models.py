
from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# CONFIGURE TABLES

class Area(db.Model):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    cafes: Mapped[list["Cafe"]] = relationship(back_populates="area")


class Cafe(db.Model):
    __tablename__ = "cafes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    price_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    wifi_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    power_outlets: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    image_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), nullable=False)
    area: Mapped["Area"] = relationship(back_populates="cafes")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class Admin(db.Model):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
