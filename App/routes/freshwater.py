# App/routes/freshwater.py

import mysql.connector
from urllib.parse import urlencode

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


def _get_max_year_for_indicator(conn, indicator_id: str):
    if not indicator_id:
        return None
    cur = conn.cursor()
    cur.execute(
        """
        SELECT MAX(year)
        FROM freshwater_data
        WHERE freshwater_indicator_id = %s
        """,
        (indicator_id,),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return row[0]


def _safe_float(x):
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _build_snapshot(conn, indicators, countries, snap_indicator_id: str, snap_year: str, snap_country_id: str):
    indicator_name = None
    unit = None
    for ind in indicators:
        if str(ind.get("freshwater_indicator_id")) == str(snap_indicator_id):
            indicator_name = ind.get("indicator_name")
            unit = ind.get("unit_of_measure")
            break

    snapshot = {
        "has_data": False,
        "indicator_id": snap_indicator_id,
        "year": snap_year,
        "indicator_name": indicator_name,
        "unit_of_measure": unit,
        "global_avg": None,
        "global_n": 0,
        "region_summary": [],
        "top10": [],
        "bottom10": [],
        "highlight": None,
        "top_labels": [],
        "top_values": [],
        "bottom_labels": [],
        "bottom_values": [],
        "region_labels": [],
        "region_avgs": [],
    }

    if not snap_indicator_id:
        return snapshot

    if not snap_year:
        max_year = _get_max_year_for_indicator(conn, snap_indicator_id)
        if max_year is not None:
            snap_year = str(max_year)
            snapshot["year"] = snap_year

    if not snap_year:
        return snapshot

    ranked_rows = []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            WITH base AS (
                SELECT
                    fd.country_id,
                    fd.freshwater_indicator_id,
                    fd.year,
                    fd.indicator_value,
                    c.country_name,
                    c.country_code,
                    c.region,
                    fi.indicator_name,
                    fi.unit_of_measure
                FROM freshwater_data fd
                JOIN countries c ON c.country_id = fd.country_id
                JOIN freshwater_indicator_details fi
                    ON fi.freshwater_indicator_id = fd.freshwater_indicator_id
                WHERE fd.freshwater_indicator_id = %s
                  AND fd.year = %s
                  AND fd.indicator_value IS NOT NULL
            ),
            ranked AS (
                SELECT
                    *,
                    RANK() OVER (ORDER BY indicator_value DESC) AS global_rank,
                    RANK() OVER (PARTITION BY region ORDER BY indicator_value DESC) AS region_rank,
                    AVG(indicator_value) OVER () AS global_avg,
                    AVG(indicator_value) OVER (PARTITION BY region) AS region_avg
                FROM base
            )
            SELECT *
            FROM ranked
            ORDER BY indicator_value DESC;
            """,
            (snap_indicator_id, snap_year),
        )
        ranked_rows = cur.fetchall()
        cur.close()
    except Exception:
        ranked_rows = []

    if not ranked_rows:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                fd.country_id,
                fd.freshwater_indicator_id,
                fd.year,
                fd.indicator_value,
                c.country_name,
                c.country_code,
                c.region,
                fi.indicator_name,
                fi.unit_of_measure
            FROM freshwater_data fd
            JOIN countries c ON c.country_id = fd.country_id
            JOIN freshwater_indicator_details fi
                ON fi.freshwater_indicator_id = fd.freshwater_indicator_id
            WHERE fd.freshwater_indicator_id = %s
              AND fd.year = %s
              AND fd.indicator_value IS NOT NULL
            """,
            (snap_indicator_id, snap_year),
        )
        base_rows = cur.fetchall()
        cur.close()

        base_rows = [r for r in base_rows if _safe_float(r.get("indicator_value")) is not None]
        base_rows.sort(key=lambda r: _safe_float(r.get("indicator_value")), reverse=True)

        if base_rows:
            total = sum(_safe_float(r.get("indicator_value")) for r in base_rows)
            n = len(base_rows)
            global_avg = total / n if n else None

            region_sum = {}
            region_count = {}
            for r in base_rows:
                reg = r.get("region") or "Unknown"
                v = _safe_float(r.get("indicator_value"))
                region_sum[reg] = region_sum.get(reg, 0.0) + (v if v is not None else 0.0)
                region_count[reg] = region_count.get(reg, 0) + 1

            last_val = None
            last_rank = 0
            for idx, r in enumerate(base_rows):
                v = _safe_float(r.get("indicator_value"))
                if last_val is None or v != last_val:
                    last_rank = idx + 1
                    last_val = v
                r["global_rank"] = last_rank
                r["global_avg"] = global_avg

            by_region = {}
            for r in base_rows:
                reg = r.get("region") or "Unknown"
                by_region.setdefault(reg, []).append(r)

            for reg, items in by_region.items():
                items.sort(key=lambda rr: _safe_float(rr.get("indicator_value")), reverse=True)
                last_val_r = None
                last_rank_r = 0
                reg_avg = (region_sum.get(reg, 0.0) / region_count.get(reg, 1)) if region_count.get(reg, 0) else None
                for idx, rr in enumerate(items):
                    vv = _safe_float(rr.get("indicator_value"))
                    if last_val_r is None or vv != last_val_r:
                        last_rank_r = idx + 1
                        last_val_r = vv
                    rr["region_rank"] = last_rank_r
                    rr["region_avg"] = reg_avg

            ranked_rows = base_rows

    if not ranked_rows:
        return snapshot

    snapshot["has_data"] = True
    snapshot["global_n"] = len(ranked_rows)
    snapshot["global_avg"] = _safe_float(ranked_rows[0].get("global_avg"))

    region_map = {}
    for r in ranked_rows:
        reg = r.get("region") or "Unknown"
        if reg not in region_map:
            region_map[reg] = {
                "region": reg,
                "avg": _safe_float(r.get("region_avg")),
                "n": 0,
            }
        region_map[reg]["n"] += 1

    region_summary = list(region_map.values())
    region_summary.sort(key=lambda x: (x["avg"] is None, -(x["avg"] or 0.0)))
    snapshot["region_summary"] = region_summary

    top10 = ranked_rows[:10]
    bottom10 = sorted(ranked_rows[-10:], key=lambda r: _safe_float(r.get("indicator_value")) or 0.0)

    snapshot["top10"] = top10
    snapshot["bottom10"] = bottom10

    if snap_country_id:
        for r in ranked_rows:
            if str(r.get("country_id")) == str(snap_country_id):
                snapshot["highlight"] = r
                break

    snapshot["top_labels"] = [f'{r.get("country_name")} ({r.get("country_code")})' for r in top10]
    snapshot["top_values"] = [_safe_float(r.get("indicator_value")) for r in top10]

    snapshot["bottom_labels"] = [f'{r.get("country_name")} ({r.get("country_code")})' for r in bottom10]
    snapshot["bottom_values"] = [_safe_float(r.get("indicator_value")) for r in bottom10]

    snapshot["region_labels"] = [r["region"] for r in region_summary]
    snapshot["region_avgs"] = [_safe_float(r["avg"]) for r in region_summary]

    return snapshot


# ---------------------------------------------------------
# LIST PAGE (with filters/search + pagination)
# ---------------------------------------------------------
@freshwater_bp.route("/", methods=["GET"])
def list_freshwater():
    country_id = request.args.get("country_id", "").strip()
    indicator_id = request.args.get("indicator_id", "").strip()
    year = request.args.get("year", "").strip()
    q = request.args.get("q", "").strip()
    sort_by = request.args.get("sort_by", "data_id").strip()
    order = request.args.get("order", "asc").strip().lower()

    snap_indicator_id = request.args.get("snap_indicator_id", "").strip()
    snap_year = request.args.get("snap_year", "").strip()
    snap_country_id = request.args.get("snap_country_id", "").strip()

    page = request.args.get("page", default=1, type=int)
    per_page = 50
    if page < 1:
        page = 1

    conn = get_db()

    countries = _get_countries()
    indicators = _get_indicators()

    if not snap_indicator_id and indicators:
        snap_indicator_id = str(indicators[0]["freshwater_indicator_id"])
    if not snap_year:
        max_year = _get_max_year_for_indicator(conn, snap_indicator_id)
        if max_year is not None:
            snap_year = str(max_year)

    snapshot = _build_snapshot(conn, indicators, countries, snap_indicator_id, snap_year, snap_country_id)

    where_sql = "WHERE 1=1"
    params = []

    if country_id:
        where_sql += " AND fd.country_id = %s"
        params.append(country_id)

    if indicator_id:
        where_sql += " AND fd.freshwater_indicator_id = %s"
        params.append(indicator_id)

    if year:
        where_sql += " AND fd.year = %s"
        params.append(year)

    if q:
        where_sql += " AND (c.country_name LIKE %s OR c.country_code LIKE %s OR fi.indicator_name LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like, like])

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM freshwater_data AS fd
        JOIN countries AS c ON fd.country_id = c.country_id
        JOIN freshwater_indicator_details AS fi
            ON fd.freshwater_indicator_id = fi.freshwater_indicator_id
        {where_sql}
    """

    cur = conn.cursor(dictionary=True)
    cur.execute(count_sql, params)
    total_count = int(cur.fetchone()["total"])
    cur.close()

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    if page > total_pages:
        page = total_pages

    allowed_sort_columns = {
        "data_id": "fd.data_id",
        "country": "c.country_name",
        "region": "c.region",
        "code": "c.country_code",
        "indicator": "fi.indicator_name",
        "unit": "fi.unit_of_measure",
        "year": "fd.year",
        "value": "fd.indicator_value",
    }

    sort_col_sql = allowed_sort_columns.get(sort_by, "fd.data_id")
    sort_dir_sql = "DESC" if order == "desc" else "ASC"

    offset = (page - 1) * per_page

    data_sql = f"""
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
        {where_sql}
        ORDER BY {sort_col_sql} {sort_dir_sql}
        LIMIT {per_page} OFFSET {offset}
    """

    cur = conn.cursor(dictionary=True)
    cur.execute(data_sql, params)
    rows = cur.fetchall()
    cur.close()

    list_reset_url = url_for(
        "freshwater.list_freshwater",
        snap_indicator_id=snap_indicator_id,
        snap_year=snap_year,
        snap_country_id=snap_country_id,
    )
    snapshot_reset_url = url_for(
        "freshwater.list_freshwater",
        q=q,
        country_id=country_id,
        indicator_id=indicator_id,
        year=year,
        sort_by=sort_by,
        order=order,
    )

    qs_params = {
        "sort_by": sort_by,
        "order": order,
        "snap_indicator_id": snap_indicator_id,
        "snap_year": snap_year,
    }
    if q:
        qs_params["q"] = q
    if country_id:
        qs_params["country_id"] = country_id
    if indicator_id:
        qs_params["indicator_id"] = indicator_id
    if year:
        qs_params["year"] = year
    if snap_country_id:
        qs_params["snap_country_id"] = snap_country_id

    base_qs = urlencode(qs_params)

    return render_template(
        "freshwater_list.html",
        rows=rows,
        countries=countries,
        indicators=indicators,
        snapshot=snapshot,
        filters={
            "country_id": country_id,
            "indicator_id": indicator_id,
            "year": year,
            "q": q,
            "sort_by": sort_by,
            "order": order,
        },
        snapshot_filters={
            "snap_indicator_id": snap_indicator_id,
            "snap_year": snap_year,
            "snap_country_id": snap_country_id,
        },
        list_reset_url=list_reset_url,
        snapshot_reset_url=snapshot_reset_url,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_count=total_count,
        base_qs=base_qs,
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


# ---------------------------------------------------------
# DELETE ACTION
# ---------------------------------------------------------
@freshwater_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_freshwater(id):
    conn = get_db()

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM freshwater_data WHERE data_id = %s", (id,))

        student_id = request.form.get("student_id") or None
        if student_id:
            audit_sql = """
                INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(audit_sql, (student_id, "DELETE", "freshwater_data", id))

        conn.commit()

        if cur.rowcount == 0:
            flash("Record not found.", "warning")
        else:
            flash("Record deleted successfully.", "success")

        cur.close()

    except Exception as e:
        conn.rollback()
        flash(f"Delete Error (freshwater): {e}", "danger")

    return redirect(url_for("freshwater.list_freshwater"))
