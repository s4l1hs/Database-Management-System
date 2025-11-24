from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from App.models import Student

login_bp = Blueprint("auth", __name__, url_prefix="/auth")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        team = session.get("team_no", 0) 
        try:
            team = int(team)
        except (TypeError, ValueError):
            team = 0

        if team != 1:
            return "Unauthorized: Admins only."
        return f(*args, **kwargs)

    return decorated_function


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Sadece admin login (team_no=1).
    Normal kullanıcı oluşturulmaz.
    """
    if request.method == "POST":
        # ⚠️ form'daki input name'i ile aynı olmalı
        sid = request.form.get("student_number", type=int)

        student = Student.query.filter_by(student_number=sid, team_no=1).first()

        if not student:
            flash("No admin was found registered with this number.", "danger")
            return redirect(url_for("auth.login"))

        # admin bulundu → session'a yaz
        session["student_number"] = student.student_number
        session["team_no"] = int(student.team_no or 0)

        return redirect(url_for("health.list_health"))

    return render_template("login.html")


@login_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
