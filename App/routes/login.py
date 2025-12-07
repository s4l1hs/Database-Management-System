# App/routes/login.py

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from App.db import get_db

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
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT student_id, student_number, full_name, team_no
            FROM students
            WHERE student_number = %s AND team_no = 1
            """,
            (entered_number,),
        )
        student = cur.fetchone()
        cur.close()

        if not student:
            flash("Admin not found.", "danger")
            return redirect(url_for("auth.login"))

        # Save login session
        session["student_id"] = student["student_id"]
        session["student_number"] = student["student_number"]
        session["team_no"] = int(student["team_no"])

        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


# -------------------------------
# Logout
# -------------------------------
@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
