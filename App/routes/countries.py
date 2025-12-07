from flask import Blueprint, render_template, request, jsonify
from App.db import db

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

    conn = db.engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.execute(base_sql, params)
        rows = cur.fetchall()
        colnames = [d[0] for d in cur.description]
    finally:
        cur.close()
        conn.close()

    return render_template(
        "country_list.html",
        rows=rows,
        colnames=colnames,
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
    conn = db.engine.raw_connection()
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
        conn.close()

    return jsonify(stats)