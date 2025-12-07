import os
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from App.db import close_db

load_dotenv()

# Project base directory (root of the repo)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
        static_folder=os.path.join(BASE_DIR, "frontend", "css"),
    )

    # ---------- SECRET KEY ----------
    app.secret_key = os.getenv("SECRET_KEY", "secret_key_wdi_team1")

    # ---------- TEARDOWN (DB CONNECTION CLOSE) ----------
    app.teardown_appcontext(close_db)

    # ---------- BLUEPRINTS ----------
    from App.routes.sustainability import sustainability_bp
    from App.routes.about import about_bp
    from App.routes.login import login_bp
    from App.routes.health import health_bp
    from App.routes.dashboard import dashboard_bp
    from App.routes.freshwater import freshwater_bp
    from App.routes.ghg import ghg_bp
    from App.routes.energy import energy_bp
    from App.routes.countries import countries_bp

    app.register_blueprint(countries_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(sustainability_bp)
    app.register_blueprint(freshwater_bp)
    app.register_blueprint(ghg_bp)
    app.register_blueprint(energy_bp)

    # ---------- ROOT: first page = login ----------
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app
