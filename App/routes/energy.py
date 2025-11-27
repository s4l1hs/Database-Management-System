from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash
from App.db import db
from App.models import EnergyData, Countries, EnergyIndicatorDetails, Student, AuditLog
from App.routes.login import admin_required

energy_bp = Blueprint("energy", __name__, url_prefix="/energy")

# ---------- LIST ----------
@energy_bp.route("/", methods=["GET"])
def list_energy():
    try:
        rows = (
            db.session.query(EnergyData, Countries, EnergyIndicatorDetails)
            .join(Countries, EnergyData.country_id == Countries.country_id)
            .join(
                EnergyIndicatorDetails,
                EnergyData.energy_indicator_id == EnergyIndicatorDetails.energy_indicator_id,
            )
            .order_by(Countries.country_name, EnergyIndicatorDetails.indicator_name, EnergyData.year)
            .all()
        )
        return render_template("energy_list.html", rows=rows)
    except Exception as e:
        return f"Database Error (energy): {e}"


# ---------- CREATE ----------
@energy_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_energy():
    if request.method == "POST":
        try:
            c_id = request.form.get("country_id")
            i_id = request.form.get("energy_indicator_id")
            year = request.form.get("year")
            val = request.form.get("indicator_value")
            note = request.form.get("data_source")
            student_id = request.form.get("student_id")

            new_data = EnergyData(
                country_id=c_id,
                energy_indicator_id=i_id,
                year=year,
                indicator_value=val,
                data_source=note
            )
            db.session.add(new_data)
            db.session.commit()

            # ---------- AUDIT LOG ----------
            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="CREATE",
                    table_name="energy_data",
                    record_id=new_data.data_id,
                )
                db.session.add(log)
                db.session.commit()

            flash("Record added successfully.", "success")
            return redirect(url_for("energy.list_energy"))

        except IntegrityError:
            db.session.rollback()
            flash("This country + indicator + year combination already exists!", "danger")
            return redirect(url_for("energy.add_energy"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("energy.add_energy"))

    return render_template(
        "energy_form.html",
        countries=Countries.query.all(),
        indicators=EnergyIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Add",
        record=None,
    )


# ---------- UPDATE ----------
@energy_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_energy(id):
    record = EnergyData.query.get_or_404(id)

    if request.method == "POST":
        try:
            record.indicator_value = request.form.get("indicator_value", type=float)
            record.year = request.form.get("year", type=int)
            record.data_source = request.form.get("data_source")
            student_id = request.form.get("student_id")

            # Audit Log
            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="UPDATE",
                    table_name="energy_data",
                    record_id=record.data_id,
                )
                db.session.add(log)

            db.session.commit()
            flash("Record updated successfully.", "success")
            return redirect(url_for("energy.list_energy"))

        except Exception as e:
            return f"Update Error (energy): {e}"

    return render_template(
        "energy_form.html",
        record=record,
        countries=Countries.query.all(),
        indicators=EnergyIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Edit",
    )


# ---------- DELETE ----------
@energy_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_energy(id):
    record = EnergyData.query.get_or_404(id)

    try:
        db.session.delete(record)
        db.session.commit()
        flash("Record deleted successfully.", "success")
    except Exception as e:
        return f"Delete Error (energy): {e}"

    return redirect(url_for("energy.list_energy"))
