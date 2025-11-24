from flask import Blueprint, render_template, request, redirect, url_for, flash
from App.db import db
from App.models import SustainabilityData, Countries, SustainabilityIndicatorDetails, Student, AuditLog
from App.routes.login import admin_required #added for admin control
sustainability_bp = Blueprint("sustainability", __name__, url_prefix="/sustainability")

# =========================================================
# 1. READ - COMPLEX JOIN 
# =========================================================
@sustainability_bp.route("/", methods=["GET"])
def list_sustainability():
    try:
        query = db.session.query(
            SustainabilityData, Countries, SustainabilityIndicatorDetails
        ).join(
            Countries, SustainabilityData.country_id == Countries.country_id
        ).join(
            SustainabilityIndicatorDetails, SustainabilityData.sus_indicator_id == SustainabilityIndicatorDetails.sus_indicator_id
        ).limit(100).all()

        return render_template('sustainability_list.html', rows=query)
    except Exception as e:
        return f"Veritabanı Hatası: {e}"

# =========================================================
# 2. CREATE  + AUDIT LOG 
# =========================================================
@sustainability_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_sustainability():
    if request.method == "POST":
        try:
            c_id = request.form.get('country_id')
            i_id = request.form.get('sus_indicator_id')
            year = request.form.get('year')
            val = request.form.get('indicator_value')
            note = request.form.get('source_note')
            
            student_id = request.form.get('student_id')

            new_data = SustainabilityData(
                country_id=c_id,
                sus_indicator_id=i_id,
                year=year,
                indicator_value=val,
                source_note=note
            )
            db.session.add(new_data)
            db.session.commit()
            
            if student_id:
                log = AuditLog(
                    student_id=student_id, 
                    action_type='CREATE', 
                    table_name='sustainability_data', 
                    record_id=new_data.data_id
                )
                db.session.add(log)
                db.session.commit()

            return redirect(url_for('sustainability.list_sustainability'))
        
        except Exception as e:
            return f"Ekleme Hatası: {e}"

    return render_template("sustainability_form.html", 
                           countries=Countries.query.all(), 
                           indicators=SustainabilityIndicatorDetails.query.all(),
                           students=Student.query.all(),
                           action="Add")

# =========================================================
# 3. UPDATE + AUDIT LOG
# =========================================================
@sustainability_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_sustainability(id):
    record = SustainabilityData.query.get_or_404(id)

    if request.method == "POST":
        try:
            record.indicator_value = request.form.get('indicator_value')
            record.year = request.form.get('year')
            record.source_note = request.form.get('source_note')
            
            student_id = request.form.get('student_id')
            
            # Log
            if student_id:
                log = AuditLog(
                    student_id=student_id, 
                    action_type='UPDATE', 
                    table_name='sustainability_data', 
                    record_id=record.data_id
                )
                db.session.add(log)
                db.session.commit()

            db.session.commit()

            return redirect(url_for('sustainability.list_sustainability'))
        except Exception as e:
            return f"Güncelleme Hatası: {e}"

    return render_template("sustainability_form.html", 
                           record=record, 
                           countries=Countries.query.all(), 
                           indicators=SustainabilityIndicatorDetails.query.all(),
                           students=Student.query.all(),
                           action="Edit")

# =========================================================
# 4. DELETE 
# =========================================================
@sustainability_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_sustainability(id):
    record = SustainabilityData.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
    except Exception as e:
        return f"Silme Hatası: {e}"
    return redirect(url_for('sustainability.list_sustainability'))