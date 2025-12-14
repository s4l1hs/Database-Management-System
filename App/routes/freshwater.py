# App/routes/freshwater.py

import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from App.db import get_db
from App.routes.login import admin_required

freshwater_bp = Blueprint("freshwater", __name__, url_prefix="/freshwater")


# ---------------------------------------------------------
# Helper queries for dropdowns
# ---------------------------------------------------------
def _get_countries():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT country_id, country_name, country_code, region
        FROM countries
        ORDER BY country_name
        """
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def _get_indicators():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT freshwater_indicator_id, indicator_name, unit_of_measure
        FROM freshwater_indicator_details
        ORDER BY indicator_name
        """
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def _get_students():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT student_id, student_number, full_name, team_no
        FROM students
        ORDER BY student_number
        """
    )
    rows = cur.fetchall()
    cur.close()
    return rows


# ---------------------------------------------------------
# LIST PAGE (with filters/search)
# ---------------------------------------------------------
@freshwater_bp.route("/", methods=["GET"])
def list_freshwater():
    country_id = request.args.get("country_id", "").strip()
    indicator_id = request.args.get("indicator_id", "").strip()
    year = request.args.get("year", "").strip()
    q = request.args.get("q", "").strip()

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            fd.data_id,
            fd.country_id,
            fd.freshwater_indicator_id,
            fd.year,
            fd.indicator_value,
            fd.source_notes,
            c.country_name,
            c.region,
            c.country_code,
            fi.indicator_name,
            fi.unit_of_measure
        FROM freshwater_data AS fd
        JOIN countries AS c ON fd.country_id = c.country_id
        JOIN freshwater_indicator_details AS fi
            ON fd.freshwater_indicator_id = fi.freshwater_indicator_id
        WHERE 1=1
    """
    params = []

    if country_id:
        sql += " AND fd.country_id = %s"
        params.append(country_id)

    if indicator_id:
        sql += " AND fd.freshwater_indicator_id = %s"
        params.append(indicator_id)

    if year:
        sql += " AND fd.year = %s"
        params.append(year)

    if q:
        sql += " AND (c.country_name LIKE %s OR c.country_code LIKE %s OR fi.indicator_name LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like, like])

    sql += " ORDER BY c.country_name, fi.indicator_name, fd.year;"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()

    return render_template(
        "freshwater_list.html",
        rows=rows,
        countries=_get_countries(),
        indicators=_get_indicators(),
        filters={
            "country_id": country_id,
            "indicator_id": indicator_id,
            "year": year,
            "q": q,
        },
    )


# ---------------------------------------------------------
# CREATE PAGE
# ---------------------------------------------------------
@freshwater_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_freshwater():
    conn = get_db()

    if request.method == "POST":
        c_id = request.form.get("country_id")
        i_id = request.form.get("freshwater_indicator_id")
        year = request.form.get("year")
        val = request.form.get("indicator_value")
        note = request.form.get("source_notes")
        student_id = request.form.get("student_id") or None

        try:
            cur = conn.cursor()

            insert_sql = """
                INSERT INTO freshwater_data
                    (country_id, freshwater_indicator_id, year, indicator_value, source_notes)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(insert_sql, (c_id, i_id, year, val, note))
            new_id = cur.lastrowid

            if student_id:
                audit_sql = """
                    INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(audit_sql, (student_id, "CREATE", "freshwater_data", new_id))

            conn.commit()
            cur.close()

            flash("Record added successfully.", "success")
            return redirect(url_for("freshwater.list_freshwater"))

        except mysql.connector.IntegrityError:
            conn.rollback()
            flash("This country + indicator + year combination already exists!", "danger")
            return redirect(url_for("freshwater.add_freshwater"))

        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("freshwater.add_freshwater"))

    return render_template(
        "freshwater_form.html",
        countries=_get_countries(),
        indicators=_get_indicators(),
        students=_get_students(),
        action="Add",
        record=None,
    )


# ---------------------------------------------------------
# UPDATE PAGE
# ---------------------------------------------------------
@freshwater_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_freshwater(id):
    conn = get_db()

    # Fetch current record
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT data_id, country_id, freshwater_indicator_id, year, indicator_value, source_notes
        FROM freshwater_data
        WHERE data_id = %s
        """,
        (id,),
    )
    record = cur.fetchone()
    cur.close()

    if record is None:
        abort(404)

    if request.method == "POST":
        try:
            indicator_value = request.form.get("indicator_value")
            year = request.form.get("year")
            source_notes = request.form.get("source_notes")
            student_id = request.form.get("student_id") or None

            cur = conn.cursor()

            update_sql = """
                UPDATE freshwater_data
                SET indicator_value = %s,
                    year = %s,
                    source_notes = %s
                WHERE data_id = %s
            """
            cur.execute(update_sql, (indicator_value, year, source_notes, id))

            if student_id:
                audit_sql = """
                    INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(audit_sql, (student_id, "UPDATE", "freshwater_data", id))

            conn.commit()
            cur.close()

            flash("Record updated successfully.", "success")
            return redirect(url_for("freshwater.list_freshwater"))

        except Exception as e:
            conn.rollback()
            return f"Update Error (freshwater): {e}"

    return render_template(
        "freshwater_form.html",
        record=record,
        countries=_get_countries(),
        indicators=_get_indicators(),
        students=_get_students(),
        action="Edit",
    )
