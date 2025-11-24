from flask import render_template, current_app


def register_views(app):
    """Register route handlers with the given Flask app."""

    @app.route("/")
    def home():
        """Render the home page."""
        return render_template("home.html")

    @app.route("/greenhouse")
    def greenhouse_list():
        """Render a page listing greenhouse gas emission data from the database."""
        db = current_app.config["DB"]
        data = db.get_greenhouse_data()
        return render_template("greenhouse_list.html", rows=data)
