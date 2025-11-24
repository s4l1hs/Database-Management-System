import os
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from App.db import db, close_db

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend", "css", "templates"),
        static_folder=os.path.join(BASE_DIR, "frontend", "css"),
    )

    # ---------- DB CONFIG ----------
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "wdi_project")
    DB_PORT = os.getenv("DB_PORT", "3306")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---------- SECRET KEY ----------
    app.secret_key = "secret_key_wdi_team1"

    # ---------- ORM INIT ----------
    db.init_app(app)

    # ---------- TEARDOWN ----------
    app.teardown_appcontext(close_db)

    # ---------- BLUEPRINTS ----------
    # from App.routes.sustainability import sustainability_bp
    from App.routes.about import about_bp
    # from App.routes.freshwater import freshwater_bp
    from App.routes.health import health_bp
    # from App.routes.ghg import ghg_bp
    # from App.routes.energy import energy_bp


    #app.register_blueprint(sustainability_bp)
    app.register_blueprint(about_bp)
    #app.register_blueprint(freshwater_bp)
    app.register_blueprint(health_bp)
    #app.register_blueprint(ghg_bp)
    #app.register_blueprint(energy_bp)

    # ---------- ROOT ----------
    @app.route("/")
    def index():
        return redirect(url_for("health.list_health"))


    return app
