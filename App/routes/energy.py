import mysql.connector
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, abort
)
from App.db import get_db
from App.routes.login import admin_required

energy_bp = Blueprint("energy", __name__, url_prefix="/energy")

# --- HELPER: Load Lists for Dropdowns ---
def _load_countries_and_indicators():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # 1. Get Countries
    cur.execute("SELECT country_id, country_name FROM countries ORDER BY country_name")
    countries = cur.fetchall()
    
    # 2. Get Energy Indicators (Using correct 'measurement_unit')
    cur.execute("""
        SELECT energy_indicator_id, indicator_name, measurement_unit 
        FROM energy_indicator_details 
        ORDER BY indicator_name
    """)
    indicators = cur.fetchall()
    
    return countries, indicators

# --- 1. READ (LIST + FILTER) ---
@energy_bp.route("/", methods=["GET"])
def list_energy():
    country_name = request.args.get("country", type=str)
    year = request.args.get("year", type=int)

    db = get_db()
    # dictionary=True is CRITICAL. It lets us access data by name in HTML
    cur = db.cursor(dictionary=True)

    # Base Query
    base_sql = """
        SELECT 
            e.data_id,
            e.country_id,
            e.energy_indicator_id,
            e.indicator_value,
            e.year,
            e.data_source,
            c.country_name,
            c.country_code,
            c.region,
            ind.indicator_name,
            ind.measurement_unit
        FROM energy_data e
        JOIN countries c ON e.country_id = c.country_id
        JOIN energy_indicator_details ind ON e.energy_indicator_id = ind.energy_indicator_id
    """

    conditions = []
    params = []

    # Filter Logic
    if country_name:
        conditions.append("c.country_name LIKE %s")
        params.append(f"%{country_name}%")
    
    if year:
        conditions.append("e.year = %s")
        params.append(year)
    
    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)
    
    # Default ordering: by primary id ascending
    base_sql += " ORDER BY e.data_id ASC LIMIT 500"

    cur.execute(base_sql, params)
    rows = cur.fetchall()

    return render_template(
        "energy_list.html",
        rows=rows,
        current_country=country_name,
        current_year=year
    )

# --- 2. CREATE (ADD) ---
@energy_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_energy():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        try:
            # Capture form data
            c_id = request.form.get("country_id", type=int)
            i_id = request.form.get("energy_indicator_id", type=int)
            year = request.form.get("year", type=int)
            val = request.form.get("indicator_value", type=float)
            note = request.form.get("data_source")

            # Insert Data
            insert_sql = """
                INSERT INTO energy_data 
                (country_id, energy_indicator_id, indicator_value, year, data_source)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(insert_sql, (c_id, i_id, val, year, note))
            new_id = cur.lastrowid # Get the ID of the row we just created
            
            # --- AUDIT LOG ---
            current_student_id = session.get("student_id")
            if current_student_id:
                audit_sql = """
                    INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(audit_sql, (current_student_id, "CREATE", "energy_data", new_id))
            
            db.commit()
            flash("Record added successfully.", "success")
            return redirect(url_for("energy.list_energy"))

        except mysql.connector.IntegrityError as e:
            db.rollback()
            if e.errno == 1062: # Duplicate entry error code
                flash("This country + indicator + year combination already exists!", "danger")
            else:
                flash(f"Database Integrity Error: {e}", "danger")
            return redirect(url_for("energy.add_energy"))
            
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("energy.add_energy"))

    # GET request: Show form
    countries, indicators = _load_countries_and_indicators()
    
    # ✅ FIX: Passing 'action' and 'record' so the form knows it is Adding
    return render_template(
        "energy_form.html", 
        countries=countries, 
        indicators=indicators, 
        action="Add", 
        record=None
    )

# --- 3. UPDATE (EDIT) ---
@energy_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_energy(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # Fetch existing record
    cur.execute("SELECT * FROM energy_data WHERE data_id = %s", (id,))
    record = cur.fetchone()

    if not record:
        abort(404)

    if request.method == "POST":
        try:
            val = request.form.get("indicator_value", type=float)
            year = request.form.get("year", type=int)
            note = request.form.get("data_source")

            update_sql = """
                UPDATE energy_data 
                SET indicator_value = %s, year = %s, data_source = %s
                WHERE data_id = %s
            """
            cur = db.cursor() # reset cursor without dictionary for standard execution
            cur.execute(update_sql, (val, year, note, id))

            # --- AUDIT LOG ---
            current_student_id = session.get("student_id")
            if current_student_id:
                audit_sql = """
                    INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(audit_sql, (current_student_id, "UPDATE", "energy_data", id))
            
            db.commit()
            flash("Record updated successfully.", "success")
            return redirect(url_for("energy.list_energy"))

        except Exception as e:
            db.rollback()
            flash(f"Update Error: {e}", "danger")

    # ✅ FIX: Loading dropdowns AND passing 'action' so the form knows it is Editing
    countries, indicators = _load_countries_and_indicators()
    return render_template(
        "energy_form.html", 
        record=record,
        countries=countries,
        indicators=indicators,
        action="Edit"
    )

# --- 4. DELETE ---
@energy_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_energy(id):
    db = get_db()
    cur = db.cursor()

    try:
        # --- AUDIT LOG (Before Delete) ---
        current_student_id = session.get("student_id")
        if current_student_id:
            audit_sql = """
                INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(audit_sql, (current_student_id, "DELETE", "energy_data", id))

        # Perform Delete
        cur.execute("DELETE FROM energy_data WHERE data_id = %s", (id,))
        db.commit()
        
        flash("Record deleted successfully.", "success")
    except Exception as e:
        db.rollback()
        flash(f"Delete Error: {e}", "danger")

    return redirect(url_for("energy.list_energy"))
    
