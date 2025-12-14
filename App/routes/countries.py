from flask import Blueprint, render_template, request, jsonify, abort
from App.db import get_db

# Blueprint tanımı
countries_bp = Blueprint("countries", __name__, url_prefix="/countries")

# =========================================================
# 1. LIST COUNTRIES (Mevcut Sayfa)
# =========================================================
@countries_bp.route("/", methods=["GET"])
def list_countries():
    """
    Common page: list all countries (name, code, region),
    optional text search on country name or code.
    """
    search = request.args.get("q", type=str)
    params = []

    base_sql = """
        SELECT country_id,
               country_name,
               country_code,
               COALESCE(region, '-') AS region
        FROM countries
    """

    where_clauses = []
    if search:
        # simple case-insensitive like: matches name OR code
        where_clauses.append("(LOWER(country_name) LIKE %s OR LOWER(country_code) LIKE %s)")
        pattern = f"%{search.lower()}%"
        params.extend([pattern, pattern])

    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    base_sql += " ORDER BY region, country_name;"

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    region_map = {}
    region_name_map = {}
    regions = []

    try:
        cur.execute(base_sql, params)
        rows = cur.fetchall()
        colnames = [d[0] for d in cur.description]

        # country_code -> region map
        cur.execute(
            """
            SELECT country_code, region
            FROM countries
            WHERE region IS NOT NULL AND region != ''
            """
        )
        code_rows = cur.fetchall()
        region_map = {(r.get("country_code") or "").upper(): r.get("region") for r in code_rows}

        # country_name -> region map (fallback for tooltip names)
        region_name_map = {
            (r.get("country_name") or ""): r.get("region") for r in rows if r.get("region")
        }

        # distinct region list
        cur.execute(
            """
            SELECT DISTINCT region
            FROM countries
            WHERE region IS NOT NULL AND region != ''
            ORDER BY region
            """
        )
        regions = [r["region"] for r in cur.fetchall()]
    finally:
        cur.close()

    return render_template(
        "country_list.html",
        rows=rows,
        colnames=colnames,
        regions=regions,
        region_map=region_map,
        region_name_map=region_name_map,
        search=search or "",
    )

# =========================================================
# 2. WIDGET API (Yeni Eklenen Kısım)
# =========================================================
@countries_bp.route("/api/stats", methods=["GET"])
def get_global_stats():
    """
    Navbar'daki widget için genel istatistikleri JSON olarak döner.
    """
    conn = get_db()
    stats = {}
    
    try:
        cur = conn.cursor(dictionary=True) # Sonuçları sözlük olarak al

        # 1. Toplam Ülke Sayısı
        cur.execute("SELECT COUNT(*) as cnt FROM countries")
        stats['total_countries'] = cur.fetchone()['cnt']

        # 2. Toplam Bölge Sayısı (Boş olmayanlar)
        cur.execute("SELECT COUNT(DISTINCT region) as cnt FROM countries WHERE region IS NOT NULL AND region != ''")
        stats['total_regions'] = cur.fetchone()['cnt']
        
        # 3. Örnek: Health tablosu varsa kayıt sayısını çek (Yoksa 0 dön)
        # Hata almamak için try-except bloğuna alabiliriz veya basitçe tablo var varsayabiliriz.
        try:
            cur.execute("SELECT COUNT(*) as cnt FROM health_system")
            stats['total_health'] = cur.fetchone()['cnt']
        except:
            stats['total_health'] = 0

    except Exception as e:
        stats = {'error': str(e)}
    finally:
        cur.close()

    return jsonify(stats)


@countries_bp.route("/api/region-stats", methods=["GET"])
def get_region_stats():
    """Return aggregated stats for a given region."""
    region = request.args.get("region")
    if not region:
        abort(400, description="region parameter is required")

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    stats = {"region": region}

    try:
        cur.execute("SELECT COUNT(*) AS cnt FROM countries WHERE region = %s", (region,))
        stats["country_count"] = cur.fetchone().get("cnt", 0)

        cur.execute(
            "SELECT country_name FROM countries WHERE region = %s ORDER BY country_name",
            (region,),
        )
        stats["countries"] = [r["country_name"] for r in cur.fetchall()]

        def _avg(query: str):
            cur.execute(query, (region,))
            val = cur.fetchone()["avg_val"]
            return float(val) if val is not None else None

        stats["avg_energy"] = _avg(
            """
            SELECT AVG(e.indicator_value) AS avg_val
            FROM energy_data e
            JOIN countries c ON c.country_id = e.country_id
            WHERE c.region = %s
            """
        )

        stats["avg_freshwater"] = _avg(
            """
            SELECT AVG(f.indicator_value) AS avg_val
            FROM freshwater_data f
            JOIN countries c ON c.country_id = f.country_id
            WHERE c.region = %s
            """
        )

        stats["avg_health"] = _avg(
            """
            SELECT AVG(h.indicator_value) AS avg_val
            FROM health_system h
            JOIN countries c ON c.country_id = h.country_id
            WHERE c.region = %s
            """
        )

        stats["avg_ghg"] = _avg(
            """
            SELECT AVG(g.indicator_value) AS avg_val
            FROM greenhouse_emissions g
            JOIN countries c ON c.country_id = g.country_id
            WHERE c.region = %s
            """
        )

        stats["avg_sustainability"] = _avg(
            """
            SELECT AVG(s.indicator_value) AS avg_val
            FROM sustainability_data s
            JOIN countries c ON c.country_id = s.country_id
            WHERE c.region = %s
            """
        )

    finally:
        cur.close()

    return jsonify(stats)