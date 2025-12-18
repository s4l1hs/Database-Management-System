import mysql.connector
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)
from App.db import get_db
from App.routes.login import admin_required

health_bp = Blueprint("health", __name__, url_prefix="/health")


# 1. READ  (LIST + FILTER)
@health_bp.route("/", methods=["GET"])
def list_health():
    country_name = request.args.get("country", type=str)
    year = request.args.get("year", type=int)

    db = get_db()
    cur = db.cursor(dictionary=True)

    base_sql = """
        SELECT
            hs.row_id,
            hs.country_id,
            hs.health_indicator_id,
            hs.indicator_value,
            hs.year,
            hs.source_notes,
            c.country_name,
            c.country_code,
            c.region,
            h.indicator_name,
            h.unit_symbol
        FROM health_system hs
        JOIN countries c
            ON c.country_id = hs.country_id
        JOIN health_indicator_details h
            ON h.health_indicator_id = hs.health_indicator_id
    """

    conditions = []
    params = []

    if country_name:
        conditions.append("c.country_name LIKE %s")
        params.append(f"%{country_name}%")

    if year:
        conditions.append("hs.year = %s")
        params.append(year)

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    # Default ordering: by primary id ascending
    base_sql += " ORDER BY hs.row_id ASC LIMIT 500"

    cur.execute(base_sql, params)
    rows = cur.fetchall()

    return render_template(
        "health_list.html",
        rows=rows,                
        current_country=country_name,
        current_year=year,
    )


# 2. HELPER: COUNTRY + INDICATOR LISTS FOR FORM
def _load_countries_and_indicators():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT country_id, country_name, country_code
        FROM countries
        ORDER BY country_name
    """)
    countries = cur.fetchall()

    cur.execute("""
        SELECT health_indicator_id, indicator_name, unit_symbol
        FROM health_indicator_details
        ORDER BY indicator_name
    """)
    indicators = cur.fetchall()

    return countries, indicators


# 3. CREATE
@health_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_health():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        try:
            c_id = request.form.get("country_id", type=int)
            i_id = request.form.get("health_indicator_id", type=int)
            year = request.form.get("year", type=int)
            val = request.form.get("indicator_value", type=float)
            note = request.form.get("source_notes")

            insert_sql = """
                INSERT INTO health_system
                    (country_id, health_indicator_id, indicator_value, year, source_notes)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(insert_sql, (c_id, i_id, val, year, note))
            db.commit()

            new_row_id = cur.lastrowid

            #  AUDIT 
            current_student_id = session.get("student_id")
            if current_student_id:
                log_sql = """
                    INSERT INTO audit_logs
                        (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(
                    log_sql,
                    (
                        current_student_id,
                        "CREATE",
                        "health_system",
                        new_row_id,
                    ),
                )
                db.commit()

            flash("Record added successfully.", "success")
            return redirect(url_for("health.list_health"))

        except mysql.connector.IntegrityError as e:
            db.rollback()
            # 1062 = duplicate key
            if e.errno == 1062:
                flash(
                    "This country + indicator + year combination already exists!",
                    "danger",
                )
            else:
                flash(f"DB Integrity error: {e}", "danger")
            return redirect(url_for("health.add_health"))

        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("health.add_health"))

    countries, indicators = _load_countries_and_indicators()
    return render_template(
        "health_form.html",
        countries=countries,
        indicators=indicators,
        action="Add",
        record=None,
    )


# 4. UPDATE
@health_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_health(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        """
        SELECT
            row_id,
            country_id,
            health_indicator_id,
            indicator_value,
            year,
            source_notes
        FROM health_system
        WHERE row_id = %s
        """,
        (id,),
    )
    record = cur.fetchone()
    if not record:
        abort(404)

    if request.method == "POST":
        try:
            indicator_value = request.form.get("indicator_value", type=float)
            year = request.form.get("year", type=int)
            source_notes = request.form.get("source_notes")

            update_sql = """
                UPDATE health_system
                SET indicator_value = %s,
                    year = %s,
                    source_notes = %s
                WHERE row_id = %s
            """
            cur.execute(update_sql, (indicator_value, year, source_notes, id))
            db.commit()

            #  AUDIT 
            current_student_id = session.get("student_id")
            if current_student_id:
                log_sql = """
                    INSERT INTO audit_logs
                        (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(
                    log_sql,
                    (
                        current_student_id,
                        "UPDATE",
                        "health_system",
                        id,
                    ),
                )
                db.commit()

            flash("Record updated successfully.", "success")
            return redirect(url_for("health.list_health"))

        except Exception as e:
            db.rollback()
            flash(f"Update Error (health): {e}", "danger")
            return redirect(url_for("health.edit_health", id=id))

    countries, indicators = _load_countries_and_indicators()
    return render_template(
        "health_form.html",
        record=record,          #dict
        countries=countries,    
        indicators=indicators,  
        action="Edit",
    )


# 5. DELETE
@health_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_health(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # check if register available
    cur.execute(
        """
        SELECT row_id
        FROM health_system
        WHERE row_id = %s
        """,
        (id,),
    )
    record = cur.fetchone()
    if not record:
        abort(404)

    try:
        #  AUDIT 
        current_student_id = session.get("student_id")
        if current_student_id:
            cur2 = db.cursor()
            log_sql = """
                INSERT INTO audit_logs
                    (student_id, action_type, table_name, record_id)
                VALUES (%s, %s, %s, %s)
            """
            cur2.execute(
                log_sql,
                (
                    current_student_id,
                    "DELETE",
                    "health_system",
                    id,
                ),
            )
            db.commit()

    
        delete_sql = "DELETE FROM health_system WHERE row_id = %s"
        cur.execute(delete_sql, (id,))
        db.commit()

        flash("Record deleted successfully.", "success")

    except Exception as e:
        db.rollback()
        return f"Error (health): {e}"

    return redirect(url_for("health.list_health"))
