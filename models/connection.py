from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    """Create tables if they do not exist."""
    db.create_all()


