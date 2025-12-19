# App/routes/login.py

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from App.db import get_db

login_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -------------------------------
# Role helpers
# -------------------------------
def get_current_role() -> str:
    """
    Map session team_no to a semantic role string.

    - viewer  (default, unauthenticated or unknown)
    - editor  (team_no == 2)
    - admin   (team_no == 1)
    """
    team = session.get("team_no", 0)
    try:
        team = int(team)
    except (TypeError, ValueError):
        team = 0

    if team == 1:
        return "admin"
    if team == 2:
        return "editor"
    return "viewer"


def editor_required(f):
    """
    Require at least editor privileges.
    Editors and admins are allowed; viewers are blocked.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = get_current_role()
        if role not in ("editor", "admin"):
            # Read-only users must not be able to POST create/update
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Require admin privileges for destructive or system-level actions.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = get_current_role()
        if role != "admin":
            abort(403)
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

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT student_id, student_number, full_name, team_no
            FROM students
            WHERE student_number = %s
            """,
            (entered_number,),
        )
        student = cur.fetchone()
        cur.close()

        if not student:
            flash("User not found.", "danger")
            return redirect(url_for("auth.login"))

        team_no = int(student.get("team_no") or 0)
        # Only known roles (admin/editor) are allowed to authenticate;
        # viewers remain unauthenticated by design.
        if team_no not in (1, 2):
            flash("You do not have permission to sign in.", "danger")
            return redirect(url_for("auth.login"))

        # Save login session
        session["student_id"] = student["student_id"]
        session["student_number"] = student["student_number"]
        session["team_no"] = team_no

        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


# -------------------------------
# Logout
# -------------------------------
@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
