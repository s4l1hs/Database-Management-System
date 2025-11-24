from flask import Blueprint, render_template, session

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    is_admin = (session.get("team_no") == 1)
    return render_template("dashboard.html", is_admin=is_admin)
