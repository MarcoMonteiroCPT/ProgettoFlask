from datetime import datetime
import json

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .connection import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    palettes = db.relationship(
        "Palette",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Palette(db.Model):
    __tablename__ = "palettes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    gpl_content = db.Column(db.Text, nullable=False)
    colors_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="palettes")

    @property
    def colors(self):
        try:
            return json.loads(self.colors_json)
        except (TypeError, ValueError):
            return []

