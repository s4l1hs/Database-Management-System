import mysql.connector
from urllib.parse import urlencode
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
from App.routes.login import admin_required, editor_required

health_bp = Blueprint("health", __name__, url_prefix="/health")

# ---------------------------------------------------------
# Yardımcı Fonksiyonlar (Dropdown ve Veri Çekme)
# ---------------------------------------------------------
def _get_countries():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT country_id, country_name, country_code, region FROM countries ORDER BY country_name")
    rows = cur.fetchall()
    cur.close()
    return rows

def _get_indicators():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT health_indicator_id, indicator_name, unit_symbol FROM health_indicator_details ORDER BY indicator_name")
    rows = cur.fetchall()
    cur.close()
    return rows

def _get_max_year_for_indicator(conn, indicator_id):
    if not indicator_id: return None
    cur = conn.cursor()
    # Şemanızda tablo adı health_system
    cur.execute("SELECT MAX(year) FROM health_system WHERE health_indicator_id = %s", (indicator_id,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None

def _safe_float(x):
    if x is None: return None
    try: return float(x)
    except: return None

# ---------------------------------------------------------
# Snapshot Analizi (Gelişmiş İstatistikler)
# ---------------------------------------------------------
def _build_snapshot(conn, indicators, countries, snap_indicator_id, snap_year, snap_country_id):
    indicator_name = None
    unit = None
    for ind in indicators:
        if str(ind.get("health_indicator_id")) == str(snap_indicator_id):
            indicator_name = ind.get("indicator_name")
            unit = ind.get("unit_symbol")
            break

    snapshot = {
        "has_data": False,
        "indicator_id": snap_indicator_id,
        "year": snap_year,
        "indicator_name": indicator_name,
        "unit_of_measure": unit, # Template uyumu için
        "global_avg": None,
        "global_n": 0,
        "region_summary": [],
        "top10": [],
        "bottom10": [],
        "highlight": None,
        "top_labels": [],
        "top_values": [],
        "region_labels": [],
        "region_avgs": [],
    }

    if not snap_indicator_id: return snapshot

    if not snap_year:
        snap_year = _get_max_year_for_indicator(conn, snap_indicator_id)
        snapshot["year"] = snap_year

    if not snap_year: return snapshot

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            WITH base AS (
                SELECT
                    hs.country_id, hs.health_indicator_id, hs.year, hs.indicator_value,
                    c.country_name, c.country_code, c.region,
                    hi.indicator_name, hi.unit_symbol
                FROM health_system hs
                JOIN countries c ON c.country_id = hs.country_id
                JOIN health_indicator_details hi ON hi.health_indicator_id = hs.health_indicator_id
                WHERE hs.health_indicator_id = %s AND hs.year = %s AND hs.indicator_value IS NOT NULL
            ),
            ranked AS (
                SELECT *,
                    RANK() OVER (ORDER BY indicator_value DESC) AS global_rank,
                    RANK() OVER (PARTITION BY region ORDER BY indicator_value DESC) AS region_rank,
                    AVG(indicator_value) OVER () AS global_avg,
                    AVG(indicator_value) OVER (PARTITION BY region) AS region_avg
                FROM base
            )
            SELECT * FROM ranked ORDER BY indicator_value DESC;
        """, (snap_indicator_id, snap_year))
        ranked_rows = cur.fetchall()
        cur.close()
    except Exception:
        ranked_rows = []

    if not ranked_rows: return snapshot

    snapshot["has_data"] = True
    snapshot["global_n"] = len(ranked_rows)
    snapshot["global_avg"] = _safe_float(ranked_rows[0].get("global_avg"))

    region_map = {}
    for r in ranked_rows:
        reg = r.get("region") or "Unknown"
        if reg not in region_map:
            region_map[reg] = {"region": reg, "avg": _safe_float(r.get("region_avg")), "n": 0}
        region_map[reg]["n"] += 1

    snapshot["region_summary"] = sorted(region_map.values(), key=lambda x: (x["avg"] is None, -(x["avg"] or 0.0)))
    snapshot["top10"] = ranked_rows[:10]
    snapshot["bottom10"] = sorted(ranked_rows[-10:], key=lambda r: _safe_float(r.get("indicator_value")) or 0.0)

    if snap_country_id:
        snapshot["highlight"] = next((r for r in ranked_rows if str(r.get("country_id")) == str(snap_country_id)), None)

    snapshot["top_labels"] = [f'{r.get("country_code")}' for r in snapshot["top10"]]
    snapshot["top_values"] = [_safe_float(r.get("indicator_value")) for r in snapshot["top10"]]
    snapshot["region_labels"] = [r["region"] for r in snapshot["region_summary"]]
    snapshot["region_avgs"] = [r["avg"] for r in snapshot["region_summary"]]

    return snapshot

# ---------------------------------------------------------
# 1. LİSTELEME (Arama + Sayfalama)
# ---------------------------------------------------------
@health_bp.route("/", methods=["GET"])
def list_health():
    # Filtreler
    country_id = request.args.get("country_id", "")
    indicator_id = request.args.get("indicator_id", "")
    year = request.args.get("year", "")
    q = request.args.get("q", "").strip()
    sort_by = request.args.get("sort_by", "row_id")
    order = request.args.get("order", "asc").lower()

    # Snapshot Filtreleri
    snap_indicator_id = request.args.get("snap_indicator_id", "")
    snap_year = request.args.get("snap_year", "")
    snap_country_id = request.args.get("snap_country_id", "")

    page = request.args.get("page", default=1, type=int)
    per_page = 50

    conn = get_db()
    countries = _get_countries()
    indicators = _get_indicators()

    if not snap_indicator_id and indicators:
        snap_indicator_id = str(indicators[0]["health_indicator_id"])
    
    snapshot = _build_snapshot(conn, indicators, countries, snap_indicator_id, snap_year, snap_country_id)

    where_sql = "WHERE 1=1"
    params = []

    if country_id:
        where_sql += " AND hs.country_id = %s"
        params.append(country_id)
    if indicator_id:
        where_sql += " AND hs.health_indicator_id = %s"
        params.append(indicator_id)
    if year:
        where_sql += " AND hs.year = %s"
        params.append(year)
    if q:
        where_sql += " AND (c.country_name LIKE %s OR c.country_code LIKE %s OR hi.indicator_name LIKE %s)"
        lq = f"%{q}%"
        params.extend([lq, lq, lq])

    cur = conn.cursor(dictionary=True)
    count_sql = f"""
        SELECT COUNT(*) AS total FROM health_system hs
        JOIN countries c ON hs.country_id = c.country_id
        JOIN health_indicator_details hi ON hs.health_indicator_id = hi.health_indicator_id
        {where_sql}
    """
    cur.execute(count_sql, params)
    total_count = int(cur.fetchone()["total"])
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    
    offset = (page - 1) * per_page
    sort_map = {"row_id": "hs.row_id", "country": "c.country_name", "value": "hs.indicator_value", "year": "hs.year"}
    sort_col = sort_map.get(sort_by, "hs.row_id")

    data_sql = f"""
        SELECT hs.*, c.country_name, c.country_code, c.region, hi.indicator_name, hi.unit_symbol
        FROM health_system hs
        JOIN countries c ON hs.country_id = c.country_id
        JOIN health_indicator_details hi ON hs.health_indicator_id = hi.health_indicator_id
        {where_sql}
        ORDER BY {sort_col} {'DESC' if order == 'desc' else 'ASC'}
        LIMIT {per_page} OFFSET {offset}
    """
    cur.execute(data_sql, params)
    rows = cur.fetchall()
    cur.close()

    base_qs = urlencode({k: v for k, v in request.args.items() if k != 'page'})

    return render_template(
        "health_list.html",
        rows=rows,
        countries=countries,
        indicators=indicators,
        snapshot=snapshot,
        filters={"country_id": country_id, "indicator_id": indicator_id, "year": year, "q": q, "sort_by": sort_by, "order": order},
        snap_filters={"snap_indicator_id": snap_indicator_id, "snap_year": snapshot["year"], "snap_country_id": snap_country_id},
        page=page, total_pages=total_pages, total_count=total_count, base_qs=base_qs
    )

# ---------------------------------------------------------
# Ekle, Düzenle, Sil İşlemleri (Audit Log Dahil)
# ---------------------------------------------------------
@health_bp.route("/add", methods=["GET", "POST"])
@editor_required
def add_health():
    if request.method == "POST":
        db = get_db()
        try:
            cur = db.cursor()
            c_id = request.form.get("country_id")
            i_id = request.form.get("health_indicator_id")
            year = request.form.get("year")
            val = request.form.get("indicator_value")
            note = request.form.get("source_notes")
            student_id = session.get("student_id")

            cur.execute("""
                INSERT INTO health_system (country_id, health_indicator_id, indicator_value, year, source_notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (c_id, i_id, val, year, note))
            new_id = cur.lastrowid

            if student_id:
                cur.execute("INSERT INTO audit_logs (student_id, action_type, table_name, record_id) VALUES (%s, %s, %s, %s)",
                            (student_id, "CREATE", "health_system", new_id))
            db.commit()
            flash("Record added successfully.", "success")
            return redirect(url_for("health.list_health"))
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
    return render_template("health_form.html", countries=_get_countries(), indicators=_get_indicators(), action="Add", record=None)

@health_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@editor_required
def edit_health(id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM health_system WHERE row_id = %s", (id,))
    record = cur.fetchone()
    if not record: abort(404)

    if request.method == "POST":
        try:
            val = request.form.get("indicator_value")
            year = request.form.get("year")
            note = request.form.get("source_notes")
            student_id = session.get("student_id")

            cur.execute("UPDATE health_system SET indicator_value=%s, year=%s, source_notes=%s WHERE row_id=%s", (val, year, note, id))
            if student_id:
                cur.execute("INSERT INTO audit_logs (student_id, action_type, table_name, record_id) VALUES (%s, %s, %s, %s)",
                            (student_id, "UPDATE", "health_system", id))
            db.commit()
            flash("Record updated.", "success")
            return redirect(url_for("health.list_health"))
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
    return render_template("health_form.html", record=record, countries=_get_countries(), indicators=_get_indicators(), action="Edit")

@health_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_health(id):
    db = get_db()
    try:
        cur = db.cursor()
        student_id = session.get("student_id")
        if student_id:
            cur.execute("INSERT INTO audit_logs (student_id, action_type, table_name, record_id) VALUES (%s, %s, %s, %s)",
                        (student_id, "DELETE", "health_system", id))
        cur.execute("DELETE FROM health_system WHERE row_id = %s", (id,))
        db.commit()
        flash("Record deleted.", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error: {e}", "danger")
    return redirect(url_for("health.list_health"))