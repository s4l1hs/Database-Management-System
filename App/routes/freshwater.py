from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash
from App.db import db
from App.models import FreshwaterData, Countries, FreshwaterIndicatorDetails, Student, AuditLog
from App.routes.login import admin_required

freshwater_bp = Blueprint("freshwater", __name__, url_prefix="/freshwater")

# ---------- LIST ----------
@freshwater_bp.route("/", methods=["GET"])
def list_freshwater():
    try:
        rows = (
            db.session.query(FreshwaterData, Countries, FreshwaterIndicatorDetails)
            .join(Countries, FreshwaterData.country_id == Countries.country_id)
            .join(
                FreshwaterIndicatorDetails,
                FreshwaterData.freshwater_indicator_id == FreshwaterIndicatorDetails.freshwater_indicator_id,
            )
            .order_by(Countries.country_name, FreshwaterIndicatorDetails.indicator_name, FreshwaterData.year)
            .all()
        )
        return render_template("freshwater_list.html", rows=rows)
    except Exception as e:
        return f"Database Error (freshwater): {e}"


# ---------- CREATE ----------
@freshwater_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_freshwater():
    if request.method == "POST":
        try:
            c_id = request.form.get("country_id")
            i_id = request.form.get("freshwater_indicator_id")
            year = request.form.get("year")
            val = request.form.get("indicator_value")
            note = request.form.get("source_notes")
            student_id = request.form.get("student_id")

            new_data = FreshwaterData(
                country_id=c_id,
                freshwater_indicator_id=i_id,
                year=year,
                indicator_value=val,
                source_notes=note
            )
            db.session.add(new_data)
            db.session.commit()

            # ---------- AUDIT LOG ----------
            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="CREATE",
                    table_name="freshwater_data",
                    record_id=new_data.data_id,
                )
                db.session.add(log)
                db.session.commit()

            flash("Record added successfully.", "success")
            return redirect(url_for("freshwater.list_freshwater"))

        except IntegrityError:
            db.session.rollback()
            flash("This country + indicator + year combination already exists!", "danger")
            return redirect(url_for("freshwater.add_freshwater"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("freshwater.add_freshwater"))

    return render_template(
        "freshwater_form.html",
        countries=Countries.query.all(),
        indicators=FreshwaterIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Add",
        record=None,
    )


# ---------- UPDATE ----------
@freshwater_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_freshwater(id):
    record = FreshwaterData.query.get_or_404(id)

    if request.method == "POST":
        try:
            record.indicator_value = request.form.get("indicator_value", type=float)
            record.year = request.form.get("year", type=int)
            record.source_notes = request.form.get("source_notes")
            student_id = request.form.get("student_id")

            # Audit Log
            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="UPDATE",
                    table_name="freshwater_data",
                    record_id=record.data_id,
                )
                db.session.add(log)

            db.session.commit()
            flash("Record updated successfully.", "success")
            return redirect(url_for("freshwater.list_freshwater"))

        except Exception as e:
            return f"Update Error (freshwater): {e}"

    return render_template(
        "freshwater_form.html",
        record=record,
        countries=Countries.query.all(),
        indicators=FreshwaterIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Edit",
    )


# ---------- DELETE ----------
@freshwater_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_freshwater(id):
    record = FreshwaterData.query.get_or_404(id)

    try:
        db.session.delete(record)
        db.session.commit()
        flash("Record deleted successfully.", "success")
    except Exception as e:
        return f"Delete Error (freshwater): {e}"

    return redirect(url_for("freshwater.list_freshwater"))
