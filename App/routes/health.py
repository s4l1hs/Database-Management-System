# App/routes/health.py

from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from App.db import db
from App.models import HealthSystem, Countries, HealthIndicatorDetails, Student, AuditLog
from App.routes.login import admin_required

# All endpoints are placed under /health
health_bp = Blueprint("health", __name__, url_prefix="/health")


# ---------- READ ----------
@health_bp.route("/", methods=["GET"])
def list_health():
    country_name = request.args.get("country", type=str)
    year = request.args.get("year", type=int)

    # ---- Base query ----
    query = (
        db.session.query(HealthSystem, Countries, HealthIndicatorDetails)
        .join(Countries, HealthSystem.country_id == Countries.country_id)
        .join(
            HealthIndicatorDetails,
            HealthSystem.health_indicator_id == HealthIndicatorDetails.health_indicator_id,
        )
    )

    # ---- Filters ----
    if country_name:
        query = query.filter(Countries.country_name.ilike(f"%{country_name}%"))

    if year:
        query = query.filter(HealthSystem.year == year)

    # LIMIT
    rows = query.order_by(Countries.country_name, HealthSystem.year).limit(500).all()

    return render_template(
        "health_list.html",
        rows=rows,
        current_country=country_name,
        current_year=year,
    )


# ---------- CREATE ----------
@health_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_health():
    if request.method == "POST":
        try:
            c_id = request.form.get("country_id")
            i_id = request.form.get("health_indicator_id")
            year = request.form.get("year")
            val = request.form.get("indicator_value")
            note = request.form.get("source_notes")

            new_data = HealthSystem(
                country_id=c_id,
                health_indicator_id=i_id,
                year=year,
                indicator_value=val,
                source_notes=note,
            )
            db.session.add(new_data)
            db.session.commit()

            # ---------- AUDIT ----------
            current_student_id = session.get("student_id")
            if current_student_id:
                log = AuditLog(
                    student_id=current_student_id,
                    action_type="CREATE",
                    table_name="health_system",
                    record_id=new_data.row_id,
                )
                db.session.add(log)
                db.session.commit()

            flash("Record added successfully.", "success")
            return redirect(url_for("health.list_health"))

        except IntegrityError:
            db.session.rollback()
            flash(
                "This country + indicator + year combination already exists!",
                "danger",
            )
            return redirect(url_for("health.add_health"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("health.add_health"))

    return render_template(
        "health_form.html",
        countries=Countries.query.all(),
        indicators=HealthIndicatorDetails.query.all(),
        students=Student.query.all(),  # İstersen bunu da kaldırabiliriz
        action="Add",
        record=None,
    )


# ---------- UPDATE ----------
@health_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_health(id):
    record = HealthSystem.query.get_or_404(id)

    if request.method == "POST":
        try:
            record.indicator_value = request.form.get("indicator_value", type=float)
            record.year = request.form.get("year", type=int)
            record.source_notes = request.form.get("source_notes")

            # ---------- AUDIT ----------
            current_student_id = session.get("student_id")
            if current_student_id:
                log = AuditLog(
                    student_id=current_student_id,
                    action_type="UPDATE",
                    table_name="health_system",
                    record_id=record.row_id,
                )
                db.session.add(log)

            db.session.commit()
            flash("Record updated successfully.", "success")
            return redirect(url_for("health.list_health"))

        except Exception as e:
            db.session.rollback()
            flash(f"Update Error (health): {e}", "danger")
            return redirect(url_for("health.edit_health", id=id))

    return render_template(
        "health_form.html",
        record=record,
        countries=Countries.query.all(),
        indicators=HealthIndicatorDetails.query.all(),
        students=Student.query.all(),  # İstersen bunu da kaldırabiliriz
        action="Edit",
    )


# ---------- DELETE ----------
@health_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_health(id):
    record = HealthSystem.query.get_or_404(id)

    try:
        # ---------- AUDIT ----------
        current_student_id = session.get("student_id")
        if current_student_id:
            log = AuditLog(
                student_id=current_student_id,
                action_type="DELETE",
                table_name="health_system",
                record_id=record.row_id,
            )
            db.session.add(log)

        db.session.delete(record)
        db.session.commit()
        flash("Record deleted successfully.", "success")

    except Exception as e:
        db.session.rollback()
        return f"Silme Hatası (health): {e}"

    return redirect(url_for("health.list_health"))
