# App/routes/login.py

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from App.models import Student

login_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -------------------------------
# Admin check decorator
# -------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        team = session.get("team_no", 0)

        try:
            team = int(team)
        except (TypeError, ValueError):
            team = 0

        if team != 1:
            return "Error: Admins only."

        return f(*args, **kwargs)

    return decorated_function


# -------------------------------
# Admin Login
# -------------------------------
@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        entered_number = request.form.get("student_number", "").strip()

        if not entered_number:
            flash("Please enter a student number.", "danger")
            return redirect(url_for("auth.login"))

        # Only admins (team_no = 1) can log in
        student = Student.query.filter_by(
            student_number=entered_number,
            team_no=1
        ).first()

        if not student:
            flash("Admin not found.", "danger")
            return redirect(url_for("auth.login"))

        # Save login session
        session["student_id"] = student.student_id
        session["student_number"] = student.student_number
        session["team_no"] = int(student.team_no)

        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


# -------------------------------
# Logout
# -------------------------------
@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
