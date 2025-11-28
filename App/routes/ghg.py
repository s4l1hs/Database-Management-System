from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash

from App.db import db
from App.models import GreenhouseGas, Countries, GhgIndicatorDetails, Student, AuditLog
from App.routes.login import admin_required  # added for admin control

ghg_bp = Blueprint("ghg", __name__, url_prefix="/ghg")


# ---------- LIST ----------
@ghg_bp.route("/", methods=["GET"])
def list_ghg():

    country_name = request.args.get("country", type=str)
    year = request.args.get("year", type=int)

    # ---- Base query ----
    query = (
        db.session.query(GreenhouseGas, Countries, GhgIndicatorDetails)
        .join(Countries, GreenhouseGas.country_id == Countries.country_id)
        .join(
            GhgIndicatorDetails,
            GreenhouseGas.ghg_indicator_id == GhgIndicatorDetails.ghg_indicator_id,
        )
    )

    # ---- Filters ----
    if country_name:
 
        query = query.filter(Countries.country_name.ilike(f"%{country_name}%"))

    if year:
        query = query.filter(GreenhouseGas.year == year)

    # LIMIT
    rows = query.order_by(Countries.country_name, GreenhouseGas.year).limit(500).all()

    return render_template(
        "ghg_list.html",
        rows=rows,
        current_country=country_name,
        current_year=year,
    )


# ---------- CREATE ----------
@ghg_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_ghg():
    if request.method == "POST":
        try:
            c_id = request.form.get("country_id")
            i_id = request.form.get("ghg_indicator_id")
            year = request.form.get("year")
            indicator_value = request.form.get("indicator_value")
            share_of_total_pct = request.form.get("share_of_total_pct")
            uncertainty_pct = request.form.get("uncertainty_pct")
            source_notes = request.form.get("source_notes")
            student_id = request.form.get("student_id")

            new_data = GreenhouseGas(
                country_id=c_id,
                ghg_indicator_id=i_id,
                year=year,
                indicator_value=indicator_value,
                share_of_total_pct=share_of_total_pct,
                uncertainty_pct=uncertainty_pct,
                source_notes=source_notes,
            )
            db.session.add(new_data)
            db.session.commit()

            # ---------- AUDIT ----------
            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="CREATE",
                    table_name="greenhouse_emissions",
                    record_id=new_data.row_id,
                )
                db.session.add(log)
                db.session.commit()

            flash("Record added successfully.", "success")
            return redirect(url_for("ghg.list_ghg"))

        except IntegrityError:
            db.session.rollback()
            flash("This country + indicator + year combination already exists!", "danger")
            return redirect(url_for("ghg.add_ghg"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("ghg.add_ghg"))

    return render_template(
        "ghg_form.html",
        countries=Countries.query.all(),
        indicators=GhgIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Add",
        record=None,
    )


# ---------- UPDATE ----------
@ghg_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_ghg(id):
    record = GreenhouseGas.query.get_or_404(id)

    if request.method == "POST":
        try:
            record.indicator_value = request.form.get("indicator_value", type=int)
            record.share_of_total_pct = request.form.get("share_of_total_pct", type=int)
            record.uncertainty_pct = request.form.get("uncertainty_pct", type=int)
            record.year = request.form.get("year", type=int)
            record.source_notes = request.form.get("source_notes")
            student_id = request.form.get("student_id")

            # Audit
            if student_id:
                log = AuditLog(
                    student_id=student_id,
                    action_type="UPDATE",
                    table_name="greenhouse_emissions",
                    record_id=record.row_id,
                )
                db.session.add(log)

            db.session.commit()
            flash("Record updated successfully.", "success")
            return redirect(url_for("ghg.list_ghg"))

        except Exception as e:
            db.session.rollback()
            flash(f"Update error: {e}", "danger")
            return redirect(url_for("ghg.edit_ghg", id=id))

    return render_template(
        "ghg_form.html",
        record=record,
        countries=Countries.query.all(),
        indicators=GhgIndicatorDetails.query.all(),
        students=Student.query.all(),
        action="Edit",
    )


# ---------- DELETE ----------
@ghg_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_ghg(id):
    record = GreenhouseGas.query.get_or_404(id)

    try:
        db.session.delete(record)
        db.session.commit()
        flash("Record deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Delete error: {e}", "danger")

    return redirect(url_for("ghg.list_ghg"))
