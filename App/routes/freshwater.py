from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, redirect, url_for, flash
from App.db import db
from App.models import FreshwaterData, Countries, FreshwaterIndicatorDetails, Student, AuditLog
from App.routes.login import admin_required

freshwater_bp = Blueprint("freshwater", __name__, url_prefix="/freshwater")

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

        except IntegrityError
