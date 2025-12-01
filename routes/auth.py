from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.connection import db
from models.model import User, Palette

auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("default.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            flash("Compila tutti i campi.", "danger")
            return redirect(url_for("auth.signup"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Esiste già un account con questa email.", "warning")
            return redirect(url_for("auth.signup"))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registrazione completata! Ora puoi accedere.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("default.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Credenziali non valide. Riprova.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=remember)
        flash("Bentornato/a!", "success")
        return redirect(url_for("default.index"))

    return render_template("auth/login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout eseguito.", "info")
    return redirect(url_for("auth.login"))


@auth.route("/profile")
@login_required
def profile():
    palettes = (
        Palette.query.filter_by(user_id=current_user.id)
        .order_by(Palette.created_at.desc())
        .all()
    )
    return render_template("auth/profile.html", palettes=palettes)


@auth.route("/profile/palettes/<int:palette_id>/delete", methods=["POST"])
@login_required
def delete_palette(palette_id: int):
    palette = Palette.query.filter_by(id=palette_id, user_id=current_user.id).first_or_404()
    db.session.delete(palette)
    db.session.commit()
    flash("Palette rimossa.", "info")
    return redirect(url_for("auth.profile"))


