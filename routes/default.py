import json
import os
from collections import Counter
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
)
from werkzeug.utils import secure_filename
from PIL import Image
from flask_login import login_required, current_user

from models.connection import db
from models.model import Palette


app = Blueprint("default", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def rgb_to_hex(rgb):
    r, g, b = rgb
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def extract_top_colors(image_path: str, num_colors: int = 6):
    img = Image.open(image_path).convert("RGB")

    # Ridimensiono per velocizzare il conteggio, mantenendo una buona approssimazione
    img = img.resize((200, 200))
    pixels = list(img.getdata())

    total_pixels = len(pixels)
    counter = Counter(pixels)
    most_common = counter.most_common(num_colors)

    colors = []
    for (r, g, b), count in most_common:
        percentage = round(count / total_pixels * 100, 2)
        colors.append(
            {
                "rgb": (r, g, b),
                "hex": rgb_to_hex((r, g, b)),
                "percentage": percentage,
            }
        )

    return colors


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    colors = None
    filename = None

    if request.method == "POST":
        if "image" not in request.files:
            flash("Nessun file inviato", "danger")
            return redirect(url_for("default.index"))

        file = request.files["image"]

        if file.filename == "":
            flash("Nessun file selezionato", "warning")
            return redirect(url_for("default.index"))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, filename)
            file.save(image_path)

            try:
                colors = extract_top_colors(image_path, num_colors=6)
            except Exception:
                flash("Errore durante l'elaborazione dell'immagine.", "danger")
                colors = None
        else:
            flash("Formato file non valido. Usa PNG, JPG, JPEG o GIF.", "danger")

    return render_template("index.html", colors=colors, filename=filename)


@app.route("/download_palette/<filename>")
@login_required
def download_palette(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, filename)

    if not os.path.exists(image_path):
        flash("Immagine non trovata.", "danger")
        return redirect(url_for("default.index"))

    colors = extract_top_colors(image_path, num_colors=6)
    base_name, _ = os.path.splitext(filename)
    palette_name = f"Palette-{base_name}"

    # Costruzione contenuto .gpl
    lines = [
        "GIMP Palette",
        f"Name: {palette_name}",
        "Columns: 6",
        "#",
    ]

    for idx, c in enumerate(colors, start=1):
        r, g, b = c["rgb"]
        name = f"Color {idx} ({c['hex']})"
        lines.append(f"{r:3d} {g:3d} {b:3d}\t{name}")

    content = "\n".join(lines) + "\n"

    colors_payload = [
        {
            "rgb": list(c["rgb"]),
            "hex": c["hex"],
            "percentage": c["percentage"],
        }
        for c in colors
    ]

    palette = (
        Palette.query.filter_by(
            user_id=current_user.id,
            image_filename=filename,
            name=palette_name,
        )
        .order_by(Palette.created_at.desc())
        .first()
    )

    if palette:
        palette.gpl_content = content
        palette.colors_json = json.dumps(colors_payload)
        palette.created_at = datetime.utcnow()
    else:
        palette = Palette(
            user_id=current_user.id,
            name=palette_name,
            image_filename=filename,
            gpl_content=content,
            colors_json=json.dumps(colors_payload),
        )
        db.session.add(palette)

    db.session.commit()

    response = Response(content, mimetype="text/plain; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="palette_{base_name}.gpl"'
    return response


@app.route("/saved_palettes/<int:palette_id>/download")
@login_required
def download_saved_palette(palette_id: int):
    palette = Palette.query.filter_by(id=palette_id, user_id=current_user.id).first_or_404()
    response = Response(palette.gpl_content, mimetype="text/plain; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{palette.name}.gpl"'
    return response



