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

sustainability_bp = Blueprint("sustainability", __name__, url_prefix="/sustainability")


# 1. READ (LIST + FILTER)
@sustainability_bp.route("/", methods=["GET"])
def list_sustainability():
    country_name = request.args.get("country", type=str)
    year = request.args.get("year", type=int)
    sort_by = request.args.get("sort_by", type=str)
    order = request.args.get("order", type=str)

    db = get_db()
    cur = db.cursor(dictionary=True)

    base_sql = """
        SELECT
            sd.data_id,
            sd.country_id,
            sd.sus_indicator_id,
            sd.indicator_value,
            sd.year,
            sd.source_note,
            c.country_name,
            c.country_code,
            c.region,
            si.indicator_name,
            si.indicator_code
        FROM sustainability_data sd
        JOIN countries c
            ON c.country_id = sd.country_id
        JOIN sustainability_indicator_details si
            ON si.sus_indicator_id = sd.sus_indicator_id
    """

    conditions = []
    params = []

    if country_name:
        conditions.append("c.country_name LIKE %s")
        params.append(f"%{country_name}%")

    if year:
        conditions.append("sd.year = %s")
        params.append(year)

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    # Sorting
    # whitelist allowed sort columns to avoid SQL injection
    allowed_sorts = {
        'country': 'c.country_name',
        'region': 'c.region',
        'indicator': 'si.indicator_name',
        'year': 'sd.year',
        'value': 'sd.indicator_value'
    }

    sort_expr = allowed_sorts.get(sort_by, 'c.country_name')
    order_keyword = 'DESC' if (order and order.lower() == 'desc') else 'ASC'

    base_sql += f" ORDER BY {sort_expr} {order_keyword}, c.country_name LIMIT 500"

    cur.execute(base_sql, params)
    rows = cur.fetchall()

    return render_template(
        "sustainability_list.html",
        rows=rows,
        current_country=country_name,
        current_year=year,
        current_sort=sort_by or 'country',
        current_order=(order or 'asc').lower(),
        sort_options=[('country','Country'),('region','Region'),('indicator','Indicator'),('year','Year'),('value','Value')],
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
        SELECT sus_indicator_id, indicator_name, indicator_code
        FROM sustainability_indicator_details
        ORDER BY indicator_name
    """)
    indicators = cur.fetchall()

    return countries, indicators


# 3. CREATE
@sustainability_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_sustainability():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        try:
            c_id = request.form.get("country_id", type=int)
            i_id = request.form.get("sus_indicator_id", type=int)
            year = request.form.get("year", type=int)
            val = request.form.get("indicator_value", type=float)
            note = request.form.get("source_note")

            insert_sql = """
                INSERT INTO sustainability_data
                    (country_id, sus_indicator_id, indicator_value, year, source_note)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(insert_sql, (c_id, i_id, val, year, note))
            db.commit()

            new_data_id = cur.lastrowid

            # AUDIT
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
                        "sustainability_data",
                        new_data_id,
                    ),
                )
                db.commit()

            flash("Record added successfully.", "success")
            return redirect(url_for("sustainability.list_sustainability"))

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
            return redirect(url_for("sustainability.add_sustainability"))

        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("sustainability.add_sustainability"))

    countries, indicators = _load_countries_and_indicators()
    return render_template(
        "sustainability_form.html",
        countries=countries,
        indicators=indicators,
        action="Add",
        record=None,
    )


# 4. UPDATE
@sustainability_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_sustainability(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        """
        SELECT
            data_id,
            country_id,
            sus_indicator_id,
            indicator_value,
            year,
            source_note
        FROM sustainability_data
        WHERE data_id = %s
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
            source_note = request.form.get("source_note")

            update_sql = """
                UPDATE sustainability_data
                SET indicator_value = %s,
                    year = %s,
                    source_note = %s
                WHERE data_id = %s
            """
            cur.execute(update_sql, (indicator_value, year, source_note, id))
            db.commit()

            # AUDIT
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
                        "sustainability_data",
                        id,
                    ),
                )
                db.commit()

            flash("Record updated successfully.", "success")
            return redirect(url_for("sustainability.list_sustainability"))

        except Exception as e:
            db.rollback()
            flash(f"Update Error (sustainability): {e}", "danger")
            return redirect(url_for("sustainability.edit_sustainability", id=id))

    countries, indicators = _load_countries_and_indicators()
    return render_template(
        "sustainability_form.html",
        record=record,  # dict
        countries=countries,
        indicators=indicators,
        action="Edit",
    )


# 5. DELETE
@sustainability_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_sustainability(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # check if record exists
    cur.execute(
        """
        SELECT data_id
        FROM sustainability_data
        WHERE data_id = %s
        """,
        (id,),
    )
    record = cur.fetchone()
    if not record:
        abort(404)

    try:
        # AUDIT
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
                    "sustainability_data",
                    id,
                ),
            )
            db.commit()

        # DELETE
        delete_sql = "DELETE FROM sustainability_data WHERE data_id = %s"
        cur.execute(delete_sql, (id,))
        db.commit()

        flash("Record deleted successfully.", "success")

    except Exception as e:
        db.rollback()
        return f"Error (sustainability): {e}"

    return redirect(url_for("sustainability.list_sustainability"))