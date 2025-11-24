from flask import Blueprint, render_template, request, redirect, url_for
from App.db import db
from App.models import (HealthSystem,Countries,HealthIndicatorDetails,Student,AuditLog,)

health_bp = Blueprint("health", __name__)


# READ - LIST + JOIN
@health_bp.route("/health", methods=["GET"])
def list_health():
    try:
        rows = (
            db.session.query(HealthSystem, Countries, HealthIndicatorDetails)
            .join(Countries, HealthSystem.country_id == Countries.country_id)
            .join(
                HealthIndicatorDetails,
                HealthSystem.health_indicator_id
                == HealthIndicatorDetails.health_indicator_id,
            )
            .limit(100)
            .all()
        )

        return render_template("health_list.html", rows=rows)
    except Exception as e:
        return f"Database Error (health): {e}"


 
# CREATE  + AUDIT LOG
@health_bp.route("/health/add", methods=["GET", "POST"])
def add_health():
    if request.method == "POST":
        try:
            c_id = request.form.get("country_id")
            i_id = request.form.get("health_indicator_id")
            year = request.form.get("year")
            val = request.form.get("indicator_value")
            note = request.form.get("source_notes")
            student_id = request.form.get("student_id")

            new_data = HealthSystem(
                country_id=c_id,
                health_indicator_id=i_id,
                year=year,
                indicator_value=val,
                source_notes=note,
            )
            db.session.add(new_data)
            db.session.commit()

            # Audit log
            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="CREATE",
                    table_name="health_system",
                    record_id=new_data.row_id,
                )
                db.session.add(log)
                db.session.commit()

            return redirect(url_for("health.list_health"))

        except Exception as e:
            return f"Ekleme Hatası (health): {e}"

    return render_template(
        "health_form.html",
        countries=Countries.query.all(),
        indicators=HealthIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Add",
        record=None,
    )



#UPDATE + AUDIT LOG
@health_bp.route("/health/edit/<int:id>", methods=["GET", "POST"])
def edit_health(id):
    record = HealthSystem.query.get_or_404(id)

    if request.method == "POST":
        try:
            record.indicator_value = request.form.get("indicator_value")
            record.year = request.form.get("year")
            record.source_notes = request.form.get("source_notes")
            student_id = request.form.get("student_id")

            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="UPDATE",
                    table_name="health_system",
                    record_id=record.row_id,
                )
                db.session.add(log)

            db.session.commit()

            return redirect(url_for("health.list_health"))

        except Exception as e:
            return f"Güncelleme Hatası (health): {e}"

    return render_template(
        "health_form.html",
        record=record,
        countries=Countries.query.all(),
        indicators=HealthIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Edit",
    )
#DELETE
@health_bp.route("/health/delete/<int:id>", methods=["POST"])
def delete_health(id):
    record = HealthSystem.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
    except Exception as e:
        return f"Silme Hatası (health): {e}"

    return redirect(url_for("health.list_health"))
