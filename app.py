import os

from flask import Flask
from flask_login import LoginManager

from models.connection import db, init_db
from models.model import User
from routes.default import app as bp_default
from routes.auth import auth as bp_auth


def create_app():
    app = Flask(__name__)

    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(base_dir, "instance")
    os.makedirs(instance_path, exist_ok=True)

    upload_folder = os.path.join(base_dir, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(instance_path, "app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Registrazione blueprint principali
    app.register_blueprint(bp_default)
    app.register_blueprint(bp_auth)

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)


