from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from mysql.connector import Error as MySQLError
from mysql.connector.errors import IntegrityError
from types import SimpleNamespace

from App.db import get_db
from App.routes.login import admin_required

ghg_bp = Blueprint("ghg", __name__, url_prefix="/ghg")


def _row_to_dict(cursor, row):
    """Convert database row to dictionary with column names as keys."""
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


def _row_to_obj(cursor, row):
    """Convert database row to SimpleNamespace object for template compatibility."""
    columns = [desc[0] for desc in cursor.description]
    return SimpleNamespace(**dict(zip(columns, row)))


# ---------- LIST ----------
@ghg_bp.route("/", methods=["GET"])
def list_ghg():
    country_name = request.args.get("country", type=str)
    year = request.args.get("year", type=int)

    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=False)

    try:
        # Base query with joins
        query = """
            SELECT 
                g.row_id,
                g.country_id,
                g.ghg_indicator_id,
                g.indicator_value,
                g.share_of_total_pct,
                g.uncertainty_pct,
                g.year,
                g.source_notes,
                c.country_id AS country_country_id,
                c.country_name,
                c.country_code,
                c.region,
                i.ghg_indicator_id AS indicator_ghg_indicator_id,
                i.indicator_name,
                i.unit_symbol
            FROM greenhouse_emissions g
            INNER JOIN countries c ON g.country_id = c.country_id
            INNER JOIN ghg_indicator_details i ON g.ghg_indicator_id = i.ghg_indicator_id
            WHERE 1=1
        """
        params = []

        # Apply filters
        if country_name:
            query += " AND c.country_name LIKE %s"
            params.append(f"%{country_name}%")

        if year:
            query += " AND g.year = %s"
            params.append(year)

        # Order and limit
        query += " ORDER BY c.country_name, g.year LIMIT 500"

        cursor.execute(query, params)
        rows_data = cursor.fetchall()

        # Convert rows to objects compatible with template
        rows = []
        for row in rows_data:
            ghg_obj = SimpleNamespace(
                row_id=row[0],
                country_id=row[1],
                ghg_indicator_id=row[2],
                indicator_value=row[3],
                share_of_total_pct=row[4],
                uncertainty_pct=row[5],
                year=row[6],
                source_notes=row[7],
            )
            country_obj = SimpleNamespace(
                country_id=row[8],
                country_name=row[9],
                country_code=row[10],
                region=row[11],
            )
            indicator_obj = SimpleNamespace(
                ghg_indicator_id=row[12],
                indicator_name=row[13],
                unit_symbol=row[14],
            )
            rows.append((ghg_obj, country_obj, indicator_obj))

    except MySQLError as e:
        flash(f"Database error: {e}", "danger")
        rows = []
    finally:
        cursor.close()

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
    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=False)

    if request.method == "POST":
        try:
            c_id = request.form.get("country_id")
            i_id = request.form.get("ghg_indicator_id")
            year = request.form.get("year")
            indicator_value = request.form.get("indicator_value")
            share_of_total_pct = request.form.get("share_of_total_pct") or None
            uncertainty_pct = request.form.get("uncertainty_pct") or None
            source_notes = request.form.get("source_notes") or None
            student_id = request.form.get("student_id") or None

            # Convert empty strings to None
            if share_of_total_pct == "":
                share_of_total_pct = None
            if uncertainty_pct == "":
                uncertainty_pct = None

            # Insert new record
            insert_query = """
                INSERT INTO greenhouse_emissions 
                (country_id, ghg_indicator_id, year, indicator_value, 
                 share_of_total_pct, uncertainty_pct, source_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    c_id,
                    i_id,
                    year,
                    indicator_value,
                    share_of_total_pct,
                    uncertainty_pct,
                    source_notes,
                ),
            )
            new_row_id = cursor.lastrowid

            # Audit log
            if student_id:
                audit_query = """
                    INSERT INTO audit_logs 
                    (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(
                    audit_query,
                    (student_id, "CREATE", "greenhouse_emissions", new_row_id),
                )

            db_conn.commit()
            flash("Record added successfully.", "success")
            return redirect(url_for("ghg.list_ghg"))

        except IntegrityError as e:
            db_conn.rollback()
            flash("This country + indicator + year combination already exists!", "danger")
            return redirect(url_for("ghg.add_ghg"))

        except MySQLError as e:
            db_conn.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("ghg.add_ghg"))

        finally:
            cursor.close()

    # GET request - fetch dropdown data
    try:
        # Fetch countries
        cursor.execute("SELECT country_id, country_name, country_code FROM countries ORDER BY country_name")
        countries_data = cursor.fetchall()
        countries = [
            SimpleNamespace(country_id=row[0], country_name=row[1], country_code=row[2])
            for row in countries_data
        ]

        # Fetch indicators
        cursor.execute(
            "SELECT ghg_indicator_id, indicator_name, unit_symbol FROM ghg_indicator_details ORDER BY indicator_name"
        )
        indicators_data = cursor.fetchall()
        indicators = [
            SimpleNamespace(
                ghg_indicator_id=row[0], indicator_name=row[1], unit_symbol=row[2]
            )
            for row in indicators_data
        ]

        # Fetch students
        cursor.execute("SELECT student_id, student_number, full_name FROM students ORDER BY student_number")
        students_data = cursor.fetchall()
        students = [
            SimpleNamespace(
                student_id=row[0], student_number=row[1], full_name=row[2]
            )
            for row in students_data
        ]

    except MySQLError as e:
        flash(f"Database error: {e}", "danger")
        countries = []
        indicators = []
        students = []
    finally:
        cursor.close()

    return render_template(
        "ghg_form.html",
        countries=countries,
        indicators=indicators,
        students=students,
        action="Add",
        record=None,
    )


# ---------- UPDATE ----------
@ghg_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_ghg(id):
    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=False)

    if request.method == "POST":
        try:
            indicator_value = request.form.get("indicator_value", type=int)
            share_val = request.form.get("share_of_total_pct")
            uncertainty_val = request.form.get("uncertainty_pct")
            share_of_total_pct = int(share_val) if share_val and share_val.strip() else None
            uncertainty_pct = int(uncertainty_val) if uncertainty_val and uncertainty_val.strip() else None
            year = request.form.get("year", type=int)
            source_notes = request.form.get("source_notes") or None
            student_id = request.form.get("student_id") or None

            # Update record
            update_query = """
                UPDATE greenhouse_emissions
                SET indicator_value = %s,
                    share_of_total_pct = %s,
                    uncertainty_pct = %s,
                    year = %s,
                    source_notes = %s
                WHERE row_id = %s
            """
            cursor.execute(
                update_query,
                (indicator_value, share_of_total_pct, uncertainty_pct, year, source_notes, id),
            )

            # Audit log
            if student_id:
                audit_query = """
                    INSERT INTO audit_logs 
                    (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(
                    audit_query,
                    (student_id, "UPDATE", "greenhouse_emissions", id),
                )

            db_conn.commit()
            flash("Record updated successfully.", "success")
            return redirect(url_for("ghg.list_ghg"))

        except MySQLError as e:
            db_conn.rollback()
            flash(f"Update error: {e}", "danger")
            return redirect(url_for("ghg.edit_ghg", id=id))

        finally:
            cursor.close()

    # GET request - fetch record and dropdown data
    try:
        # Fetch the record
        cursor.execute(
            """
            SELECT row_id, country_id, ghg_indicator_id, indicator_value,
                   share_of_total_pct, uncertainty_pct, year, source_notes
            FROM greenhouse_emissions
            WHERE row_id = %s
        """,
            (id,),
        )
        record_data = cursor.fetchone()

        if not record_data:
            abort(404)

        record = SimpleNamespace(
            row_id=record_data[0],
            country_id=record_data[1],
            ghg_indicator_id=record_data[2],
            indicator_value=record_data[3],
            share_of_total_pct=record_data[4],
            uncertainty_pct=record_data[5],
            year=record_data[6],
            source_notes=record_data[7],
        )

        # Fetch countries
        cursor.execute("SELECT country_id, country_name, country_code FROM countries ORDER BY country_name")
        countries_data = cursor.fetchall()
        countries = [
            SimpleNamespace(country_id=row[0], country_name=row[1], country_code=row[2])
            for row in countries_data
        ]

        # Fetch indicators
        cursor.execute(
            "SELECT ghg_indicator_id, indicator_name, unit_symbol FROM ghg_indicator_details ORDER BY indicator_name"
        )
        indicators_data = cursor.fetchall()
        indicators = [
            SimpleNamespace(
                ghg_indicator_id=row[0], indicator_name=row[1], unit_symbol=row[2]
            )
            for row in indicators_data
        ]

        # Fetch students
        cursor.execute("SELECT student_id, student_number, full_name FROM students ORDER BY student_number")
        students_data = cursor.fetchall()
        students = [
            SimpleNamespace(
                student_id=row[0], student_number=row[1], full_name=row[2]
            )
            for row in students_data
        ]

    except MySQLError as e:
        flash(f"Database error: {e}", "danger")
        abort(500)
    finally:
        cursor.close()

    return render_template(
        "ghg_form.html",
        record=record,
        countries=countries,
        indicators=indicators,
        students=students,
        action="Edit",
    )


# ---------- DELETE ----------
@ghg_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_ghg(id):
    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=False)

    try:
        # Check if record exists
        cursor.execute("SELECT row_id FROM greenhouse_emissions WHERE row_id = %s", (id,))
        if not cursor.fetchone():
            abort(404)

        # Delete record
        cursor.execute("DELETE FROM greenhouse_emissions WHERE row_id = %s", (id,))
        db_conn.commit()
        flash("Record deleted successfully.", "success")

    except MySQLError as e:
        db_conn.rollback()
        flash(f"Delete error: {e}", "danger")
    finally:
        cursor.close()

    return redirect(url_for("ghg.list_ghg"))
