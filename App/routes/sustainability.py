from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from App.db import db
from App.models import (
    SustainabilityData,
    Countries,
    SustainabilityIndicatorDetails,
    Student,
    AuditLog,
)
from App.routes.login import admin_required


sustainability_bp = Blueprint("sustainability", __name__, url_prefix="/sustainability")


@sustainability_bp.route("/", methods=["GET"])
def list_sustainability():
    try:
        query = (
            db.session.query(SustainabilityData, Countries, SustainabilityIndicatorDetails)
            .join(Countries, SustainabilityData.country_id == Countries.country_id)
            .join(
                SustainabilityIndicatorDetails,
                SustainabilityData.sus_indicator_id == SustainabilityIndicatorDetails.sus_indicator_id,
            )
            .order_by(Countries.country_name, SustainabilityIndicatorDetails.indicator_name, SustainabilityData.year)
            .all()
        )

        rows = [(r[0], r[1], r[2]) for r in query]
        return render_template("sustainability_list.html", rows=rows)
    except Exception as e:
        return f"Database error: {e}"


@sustainability_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_sustainability():
    if request.method == "POST":
        try:
            c_id = int(request.form.get("country_id"))
            i_id = int(request.form.get("sus_indicator_id"))
            year = int(request.form.get("year"))
            val = float(request.form.get("indicator_value"))
            note = request.form.get("source_note")

            new_data = SustainabilityData(
                country_id=c_id,
                sus_indicator_id=i_id,
                year=year,
                indicator_value=val,
                source_note=note,
            )
            db.session.add(new_data)
            db.session.commit()

            student_number = session.get("student_number")
            if student_number:
                student = Student.query.filter_by(student_number=student_number).first()
                if student:
                    log = AuditLog(
                        student_id=student.student_id,
                        action_type="CREATE",
                        table_name="sustainability_data",
                        record_id=new_data.data_id,
                    )
                    db.session.add(log)
                    db.session.commit()

            flash("Record added.", "success")
            return redirect(url_for("sustainability.list_sustainability"))
        except Exception as e:
            db.session.rollback()
            flash(f"Add error: {e}", "danger")

    return render_template(
        "sustainability_form.html",
        countries=Countries.query.order_by(Countries.country_name).all(),
        indicators=SustainabilityIndicatorDetails.query.order_by(SustainabilityIndicatorDetails.indicator_name).all(),
        action="Add",
    )


@sustainability_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_sustainability(id):
    record = SustainabilityData.query.get_or_404(id)
    if request.method == "POST":
        try:
            record.indicator_value = float(request.form.get("indicator_value"))
            record.year = int(request.form.get("year"))
            record.source_note = request.form.get("source_note")
            db.session.commit()

            student_number = session.get("student_number")
            if student_number:
                student = Student.query.filter_by(student_number=student_number).first()
                if student:
                    log = AuditLog(
                        student_id=student.student_id,
                        action_type="UPDATE",
                        table_name="sustainability_data",
                        record_id=record.data_id,
                    )
                    db.session.add(log)
                    db.session.commit()

            flash("Record updated.", "success")
            return redirect(url_for("sustainability.list_sustainability"))
        except Exception as e:
            db.session.rollback()
            flash(f"Update error: {e}", "danger")

    return render_template(
        "sustainability_form.html",
        record=record,
        countries=Countries.query.order_by(Countries.country_name).all(),
        indicators=SustainabilityIndicatorDetails.query.order_by(SustainabilityIndicatorDetails.indicator_name).all(),
        action="Edit",
    )


@sustainability_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_sustainability(id):
    record = SustainabilityData.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
        # audit
        student_number = session.get("student_number")
        if student_number:
            student = Student.query.filter_by(student_number=student_number).first()
            if student:
                log = AuditLog(
                    student_id=student.student_id,
                    action_type="DELETE",
                    table_name="sustainability_data",
                    record_id=id,
                )
                db.session.add(log)
                db.session.commit()

        flash("Record deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Delete error: {e}", "danger")

    return redirect(url_for("sustainability.list_sustainability"))