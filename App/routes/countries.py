from flask import Blueprint, render_template, request, jsonify, abort,redirect,url_for
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

    Additionally, we annotate each country with a backend-derived
    data availability flag (data_count) so the UI can disable
    navigation for countries that have zero records across all
    main datasets.
    """
    search = request.args.get("q", type=str)
    params = []

    base_sql = """
        SELECT
            c.country_id,
            c.country_name,
            c.country_code,
            COALESCE(c.region, '-') AS region,
            (
                COALESCE((
                    SELECT COUNT(*) FROM health_system hs
                    WHERE hs.country_id = c.country_id
                ), 0) +
                COALESCE((
                    SELECT COUNT(*) FROM energy_data ed
                    WHERE ed.country_id = c.country_id
                ), 0) +
                COALESCE((
                    SELECT COUNT(*) FROM freshwater_data fd
                    WHERE fd.country_id = c.country_id
                ), 0) +
                COALESCE((
                    SELECT COUNT(*) FROM greenhouse_emissions ge
                    WHERE ge.country_id = c.country_id
                ), 0) +
                COALESCE((
                    SELECT COUNT(*) FROM sustainability_data sd
                    WHERE sd.country_id = c.country_id
                ), 0)
            ) AS data_count
        FROM countries c
    """

    where_clauses = []
    if search:
        # simple case-insensitive like: matches name OR code
        where_clauses.append("(LOWER(c.country_name) LIKE %s OR LOWER(c.country_code) LIKE %s)")
        pattern = f"%{search.lower()}%"
        params.extend([pattern, pattern])

    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    # Default ordering: by primary id ascending
    base_sql += " ORDER BY c.country_id ASC"

    # Server-side pagination
    page = request.args.get('page', 1, type=int) or 1
    page_size = 8

    # count total (respect search)
    count_sql = "SELECT COUNT(*) as cnt FROM countries c"
    if where_clauses:
        count_sql += " WHERE " + " AND ".join(where_clauses)

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    region_map = {}
    region_name_map = {}
    regions = []
    has_data_by_iso2 = {}

    try:
        # get paged rows for listing
        params_for_count = list(params)
        cur.execute(count_sql, params_for_count)
        total_count = cur.fetchone().get('cnt', 0)
        total_pages = max(1, -(-int(total_count) // page_size))

        offset = (page - 1) * page_size
        params_for_rows = list(params) + [page_size, offset]
        # use LIMIT/OFFSET for pagination
        paged_sql = base_sql + " LIMIT %s OFFSET %s"
        cur.execute(paged_sql, params_for_rows)
        rows = cur.fetchall()
        colnames = [d[0] for d in cur.description]

        # country_code -> region map (full set)
        cur.execute(
            """
            SELECT country_code, region, country_name
            FROM countries
            WHERE region IS NOT NULL AND region != ''
            """
        )
        code_rows = cur.fetchall()
        region_map = {(r.get("country_code") or "").upper(): r.get("region") for r in code_rows}

        # country_name -> region map (full set)
        region_name_map = { (r.get('country_name') or ''): r.get('region') for r in code_rows if r.get('region') }

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

        # Build ISO2 -> has_data map for the frontend map widget.
        # Query full country dataset to determine availability for the map
        cur.execute("""
            SELECT c.country_code,
                (
                    COALESCE((SELECT COUNT(*) FROM health_system hs WHERE hs.country_id = c.country_id),0) +
                    COALESCE((SELECT COUNT(*) FROM energy_data ed WHERE ed.country_id = c.country_id),0) +
                    COALESCE((SELECT COUNT(*) FROM freshwater_data fd WHERE fd.country_id = c.country_id),0) +
                    COALESCE((SELECT COUNT(*) FROM greenhouse_emissions ge WHERE ge.country_id = c.country_id),0) +
                    COALESCE((SELECT COUNT(*) FROM sustainability_data sd WHERE sd.country_id = c.country_id),0)
                ) as data_count
            FROM countries c
        """)
        iso3_to_iso2 = {v: k for k, v in ISO2_TO_ISO3.items()}
        for r in cur.fetchall():
            iso3 = (r.get('country_code') or '').upper()
            iso2 = iso3_to_iso2.get(iso3)
            if not iso2:
                continue
            has_data_by_iso2[iso2] = (r.get('data_count') or 0) > 0
    finally:
        cur.close()

    return render_template(
        "country_list.html",
        rows=rows,
        colnames=colnames,
        regions=regions,
        region_map=region_map,
        region_name_map=region_name_map,
        has_data_by_iso2=has_data_by_iso2,
        search=search or "",
        current_page=page,
        total_pages=total_pages,
        total_count=total_count,
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
    """Return aggregated stats for a given region, grouped by indicator type."""
    region = request.args.get("region")
    if not region:
        abort(400, description="region parameter is required")

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    stats = {
        "region": region,
        "countries": [], 
        "energy": [],
        "health": [],
        "freshwater": [],
        "ghg": [],
        "sustainability": []
    }

    try:
        # --- 0. List of Countries ---
        cur.execute("SELECT country_name FROM countries WHERE region = %s ORDER BY country_name", (region,))
        country_rows = cur.fetchall()
        stats["countries"] = [row["country_name"] for row in country_rows]


        # --- 1. Energy Stats ---
        cur.execute("""
            SELECT d.indicator_name, d.measurement_unit as unit, AVG(e.indicator_value) as avg_val
            FROM energy_data e
            JOIN energy_indicator_details d ON e.energy_indicator_id = d.energy_indicator_id
            JOIN countries c ON e.country_id = c.country_id
            WHERE c.region = %s
            GROUP BY d.indicator_name, d.measurement_unit
            ORDER BY d.indicator_name
        """, (region,))
        stats["energy"] = cur.fetchall()

        # --- 2. Health Stats ---
        cur.execute("""
            SELECT d.indicator_name, d.unit_symbol as unit, AVG(h.indicator_value) as avg_val
            FROM health_system h
            JOIN health_indicator_details d ON h.health_indicator_id = d.health_indicator_id
            JOIN countries c ON h.country_id = c.country_id
            WHERE c.region = %s
            GROUP BY d.indicator_name, d.unit_symbol
            ORDER BY d.indicator_name
        """, (region,))
        stats["health"] = cur.fetchall()

        # --- 3. Freshwater Stats ---
        cur.execute("""
            SELECT d.indicator_name, d.unit_of_measure as unit, AVG(f.indicator_value) as avg_val
            FROM freshwater_data f
            JOIN freshwater_indicator_details d ON f.freshwater_indicator_id = d.freshwater_indicator_id
            JOIN countries c ON f.country_id = c.country_id
            WHERE c.region = %s
            GROUP BY d.indicator_name, d.unit_of_measure
            ORDER BY d.indicator_name
        """, (region,))
        stats["freshwater"] = cur.fetchall()

        # --- 4. GHG Stats ---
        cur.execute("""
            SELECT d.indicator_name, d.unit_symbol as unit, AVG(g.indicator_value) as avg_val
            FROM greenhouse_emissions g
            JOIN ghg_indicator_details d ON g.ghg_indicator_id = d.ghg_indicator_id
            JOIN countries c ON g.country_id = c.country_id
            WHERE c.region = %s
            GROUP BY d.indicator_name, d.unit_symbol
            ORDER BY d.indicator_name
        """, (region,))
        stats["ghg"] = cur.fetchall()

        # --- 5. Sustainability Stats ---
        cur.execute("""
            SELECT d.indicator_name, 'Index' as unit, AVG(s.indicator_value) as avg_val
            FROM sustainability_data s
            JOIN sustainability_indicator_details d ON s.sus_indicator_id = d.sus_indicator_id
            JOIN countries c ON s.country_id = c.country_id
            WHERE c.region = %s
            GROUP BY d.indicator_name
            ORDER BY d.indicator_name
        """, (region,))
        stats["sustainability"] = cur.fetchall()

    finally:
        cur.close()

    return jsonify(stats)


@countries_bp.route("/api/has-data/<string:iso2>", methods=["GET"])
def api_has_data(iso2: str):
    """
    Lightweight API used by the Countries tab & world map to determine
    whether a given ISO2 country has any records across the main datasets.

    This mirrors the logic in /countries/resolve, but returns JSON instead
    of redirecting or rendering a template.
    """
    iso2 = iso2.upper()
    iso3 = ISO2_TO_ISO3.get(iso2)
    if not iso3:
        # Unknown mapping – treat as no data, but do not error.
        return jsonify({"iso2": iso2, "has_data": False, "country_id": None})

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Find country row by ISO3 code stored in DB
    cur.execute(
        """
        SELECT country_id
        FROM countries
        WHERE UPPER(country_code) = %s
        LIMIT 1
        """,
        (iso3,),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        return jsonify({"iso2": iso2, "has_data": False, "country_id": None})

    country_id = row["country_id"]

    total = 0
    try:
        for tbl in (
            "health_system",
            "energy_data",
            "freshwater_data",
            "greenhouse_emissions",
            "sustainability_data",
        ):
            try:
                cur.execute(f"SELECT COUNT(*) AS cnt FROM {tbl} WHERE country_id = %s", (country_id,))
                cnt = cur.fetchone().get("cnt", 0)
                total += int(cnt or 0)
            except Exception:
                # ignore missing tables or other issues and continue
                continue
    finally:
        cur.close()

    return jsonify(
        {
            "iso2": iso2,
            "country_id": country_id,
            "has_data": total > 0,
        }
    )


@countries_bp.route("/profile/<int:country_id>", methods=["GET"])
def country_profile(country_id: int):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # Country header
    cur.execute("""
        SELECT country_id, country_name, country_code, region
        FROM countries
        WHERE country_id = %s
        LIMIT 1
    """, (country_id,))
    country = cur.fetchone()
    if not country:
        cur.close()
        return render_template(
            "country_no_data.html",
            message="Country not found."
        )

    # HEALTH
    cur.execute("""
        SELECT
            hs.row_id AS id,
            hs.year,
            hs.indicator_value AS value,
            hs.source_notes AS note,
            hid.indicator_name AS indicator,
            hid.unit_symbol AS unit
        FROM health_system hs
        JOIN health_indicator_details hid
          ON hid.health_indicator_id = hs.health_indicator_id
        WHERE hs.country_id = %s
        ORDER BY hs.year DESC, hid.indicator_name
        LIMIT 500
    """, (country_id,))
    health = cur.fetchall()

    # ENERGY
    cur.execute("""
        SELECT
            ed.data_id AS id,
            ed.year,
            ed.indicator_value AS value,
            ed.data_source AS note,
            eid.indicator_name AS indicator,
            eid.measurement_unit AS unit
        FROM energy_data ed
        JOIN energy_indicator_details eid
          ON eid.energy_indicator_id = ed.energy_indicator_id
        WHERE ed.country_id = %s
        ORDER BY ed.year DESC, eid.indicator_name
        LIMIT 500
    """, (country_id,))
    energy = cur.fetchall()

    # FRESHWATER
    cur.execute("""
        SELECT
            fd.data_id AS id,
            fd.year,
            fd.indicator_value AS value,
            fd.source_notes AS note,
            fid.indicator_name AS indicator,
            fid.unit_of_measure AS unit
        FROM freshwater_data fd
        JOIN freshwater_indicator_details fid
          ON fid.freshwater_indicator_id = fd.freshwater_indicator_id
        WHERE fd.country_id = %s
        ORDER BY fd.year DESC, fid.indicator_name
        LIMIT 500
    """, (country_id,))
    freshwater = cur.fetchall()

    # GHG
    cur.execute("""
        SELECT
            ge.row_id AS id,
            ge.year,
            ge.indicator_value AS value,
            ge.source_notes AS note,
            gid.indicator_name AS indicator,
            gid.unit_symbol AS unit
        FROM greenhouse_emissions ge
        JOIN ghg_indicator_details gid
          ON gid.ghg_indicator_id = ge.ghg_indicator_id
        WHERE ge.country_id = %s
        ORDER BY ge.year DESC, gid.indicator_name
        LIMIT 500
    """, (country_id,))
    ghg = cur.fetchall()

    # SUSTAINABILITY
    cur.execute("""
        SELECT
            sd.data_id AS id,
            sd.year,
            sd.indicator_value AS value,
            sd.source_note AS note,
            sid.indicator_name AS indicator,
            NULL AS unit
        FROM sustainability_data sd
        JOIN sustainability_indicator_details sid
          ON sid.sus_indicator_id = sd.sus_indicator_id
        WHERE sd.country_id = %s
        ORDER BY sd.year DESC, sid.indicator_name
        LIMIT 500
    """, (country_id,))
    sustainability = cur.fetchall()

    return render_template(
        "country_profile.html",
        country=country,
        health=health,
        energy=energy,
        freshwater=freshwater,
        ghg=ghg,
        sustainability=sustainability,
    )

@countries_bp.route("/region/<string:region_name>", methods=["GET"])
def region_profile(region_name: str):
    """Region profile page with aggregated data across all domains.
    Region information is derived exclusively from countries.region column."""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Verify region exists in countries table
    cur.execute("""
        SELECT DISTINCT region
        FROM countries
        WHERE region = %s
        LIMIT 1
    """, (region_name,))
    region_check = cur.fetchone()
    if not region_check:
        cur.close()
        return render_template(
            "country_no_data.html",
            message=f"Region not found: {region_name}"
        )
    
    region = {"region": region_name}
    
    # Get countries in this region for the listing table
    cur.execute("""
        SELECT 
            country_id,
            country_name,
            country_code
        FROM countries
        WHERE region = %s
        ORDER BY country_name
    """, (region_name,))
    region_countries = cur.fetchall()
    
    # HEALTH - Region-level aggregation
    cur.execute("""
        SELECT
            hid.indicator_name AS indicator,
            hid.unit_symbol AS unit,
            hs.year,
            AVG(hs.indicator_value) AS avg_value,
            MIN(hs.indicator_value) AS min_value,
            MAX(hs.indicator_value) AS max_value,
            COUNT(DISTINCT hs.country_id) AS country_count
        FROM health_system hs
        JOIN health_indicator_details hid ON hid.health_indicator_id = hs.health_indicator_id
        JOIN countries c ON c.country_id = hs.country_id
        WHERE c.region = %s AND hs.indicator_value IS NOT NULL
        GROUP BY hid.indicator_name, hid.unit_symbol, hs.year
        ORDER BY hs.year DESC, hid.indicator_name
        LIMIT 500
    """, (region_name,))
    health = cur.fetchall()
    
    # ENERGY - Region-level aggregation
    cur.execute("""
        SELECT
            eid.indicator_name AS indicator,
            eid.measurement_unit AS unit,
            ed.year,
            AVG(ed.indicator_value) AS avg_value,
            MIN(ed.indicator_value) AS min_value,
            MAX(ed.indicator_value) AS max_value,
            COUNT(DISTINCT ed.country_id) AS country_count
        FROM energy_data ed
        JOIN energy_indicator_details eid ON eid.energy_indicator_id = ed.energy_indicator_id
        JOIN countries c ON c.country_id = ed.country_id
        WHERE c.region = %s AND ed.indicator_value IS NOT NULL
        GROUP BY eid.indicator_name, eid.measurement_unit, ed.year
        ORDER BY ed.year DESC, eid.indicator_name
        LIMIT 500
    """, (region_name,))
    energy = cur.fetchall()
    
    # FRESHWATER - Region-level aggregation
    cur.execute("""
        SELECT
            fid.indicator_name AS indicator,
            fid.unit_of_measure AS unit,
            fd.year,
            AVG(fd.indicator_value) AS avg_value,
            MIN(fd.indicator_value) AS min_value,
            MAX(fd.indicator_value) AS max_value,
            COUNT(DISTINCT fd.country_id) AS country_count
        FROM freshwater_data fd
        JOIN freshwater_indicator_details fid ON fid.freshwater_indicator_id = fd.freshwater_indicator_id
        JOIN countries c ON c.country_id = fd.country_id
        WHERE c.region = %s AND fd.indicator_value IS NOT NULL
        GROUP BY fid.indicator_name, fid.unit_of_measure, fd.year
        ORDER BY fd.year DESC, fid.indicator_name
        LIMIT 500
    """, (region_name,))
    freshwater = cur.fetchall()
    
    # GHG - Region-level aggregation
    cur.execute("""
        SELECT
            gid.indicator_name AS indicator,
            gid.unit_symbol AS unit,
            ge.year,
            AVG(ge.indicator_value) AS avg_value,
            MIN(ge.indicator_value) AS min_value,
            MAX(ge.indicator_value) AS max_value,
            COUNT(DISTINCT ge.country_id) AS country_count
        FROM greenhouse_emissions ge
        JOIN ghg_indicator_details gid ON gid.ghg_indicator_id = ge.ghg_indicator_id
        JOIN countries c ON c.country_id = ge.country_id
        WHERE c.region = %s AND ge.indicator_value IS NOT NULL
        GROUP BY gid.indicator_name, gid.unit_symbol, ge.year
        ORDER BY ge.year DESC, gid.indicator_name
        LIMIT 500
    """, (region_name,))
    ghg = cur.fetchall()
    
    # SUSTAINABILITY - Region-level aggregation
    cur.execute("""
        SELECT
            sid.indicator_name AS indicator,
            NULL AS unit,
            sd.year,
            AVG(sd.indicator_value) AS avg_value,
            MIN(sd.indicator_value) AS min_value,
            MAX(sd.indicator_value) AS max_value,
            COUNT(DISTINCT sd.country_id) AS country_count
        FROM sustainability_data sd
        JOIN sustainability_indicator_details sid ON sid.sus_indicator_id = sd.sus_indicator_id
        JOIN countries c ON c.country_id = sd.country_id
        WHERE c.region = %s AND sd.indicator_value IS NOT NULL
        GROUP BY sid.indicator_name, sd.year
        ORDER BY sd.year DESC, sid.indicator_name
        LIMIT 500
    """, (region_name,))
    sustainability = cur.fetchall()
    
    # Get country-level metrics for sorting (using GHG CO2 per capita as default)
    # Countries with missing data are placed at the bottom (NULLS LAST)
    # This will be used to sort countries in the region listing
    cur.execute("""
        SELECT
            c.country_id,
            c.country_name,
            c.country_code,
            AVG(CASE WHEN ge.ghg_indicator_id = 6 THEN ge.indicator_value END) AS co2_per_capita_avg
        FROM countries c
        LEFT JOIN greenhouse_emissions ge ON c.country_id = ge.country_id AND ge.ghg_indicator_id = 6 AND ge.indicator_value IS NOT NULL
        WHERE c.region = %s
        GROUP BY c.country_id, c.country_name, c.country_code
        ORDER BY 
            CASE WHEN AVG(CASE WHEN ge.ghg_indicator_id = 6 THEN ge.indicator_value END) IS NULL THEN 1 ELSE 0 END,
            AVG(CASE WHEN ge.ghg_indicator_id = 6 THEN ge.indicator_value END) DESC NULLS LAST,
            c.country_name
    """, (region_name,))
    countries_with_metrics = cur.fetchall()
    
    cur.close()
    
    return render_template(
        "region_profile.html",
        region=region,
        health=health,
        energy=energy,
        freshwater=freshwater,
        ghg=ghg,
        sustainability=sustainability,
        countries=countries_with_metrics,
        region_countries=region_countries
    )


@countries_bp.route("/resolve/<string:iso2>", methods=["GET"])
def resolve_country(iso2):
    iso2 = iso2.upper()
    iso3 = ISO2_TO_ISO3.get(iso2)
    if not iso3:
        # show friendly no-data page instead of 404 for unmapped codes
        return render_template(
            "country_no_data.html",
            message=f"Country code not mapped: {iso2}"
        )

    db = get_db()
    cur = db.cursor(dictionary=True)

    # DB'de ISO3 tutuluyor diye country_code üzerinden arıyoruz
    cur.execute("""
        SELECT country_id
        FROM countries
        WHERE UPPER(country_code) = %s
        LIMIT 1
    """, (iso3,))

    row = cur.fetchone()
    if not row:
        cur.close()
        return render_template(
            "country_no_data.html",
            message=f"Country not found for ISO3: {iso3}"
        )

    country_id = row["country_id"]

    # Check whether this country has any recorded data across main data tables
    total = 0
    try:
        for tbl in (
            'health_system',
            'energy_data',
            'freshwater_data',
            'greenhouse_emissions',
            'sustainability_data',
        ):
            try:
                cur.execute(f"SELECT COUNT(*) AS cnt FROM {tbl} WHERE country_id = %s", (country_id,))
                cnt = cur.fetchone().get('cnt', 0)
                total += int(cnt or 0)
            except Exception:
                # ignore missing tables or other issues and continue
                continue
    finally:
        cur.close()

    if total == 0:
        # No data: show a friendly message instead of redirecting to an empty profile
        db2 = get_db()
        cur2 = db2.cursor(dictionary=True)
        try:
            cur2.execute(
                """
                SELECT country_id, country_name, country_code, region
                FROM countries
                WHERE country_id = %s
                LIMIT 1
                """,
                (country_id,)
            )
            country = cur2.fetchone()
        finally:
            cur2.close()

        return render_template(
            "country_no_data.html",
            country=country,
            message="There is no recorded data for this country."
        )

    return redirect(url_for("countries.country_profile", country_id=country_id))

ISO2_TO_ISO3 ={
  "AF": "AFG",
  "AL": "ALB",
  "DZ": "DZA",
  "AS": "ASM",
  "AD": "AND",
  "AO": "AGO",
  "AI": "AIA",
  "AQ": "ATA",
  "AG": "ATG",
  "AR": "ARG",
  "AM": "ARM",
  "AW": "ABW",
  "AU": "AUS",
  "AT": "AUT",
  "AZ": "AZE",
  "BS": "BHS",
  "BH": "BHR",
  "BD": "BGD",
  "BB": "BRB",
  "BY": "BLR",
  "BE": "BEL",
  "BZ": "BLZ",
  "BJ": "BEN",
  "BM": "BMU",
  "BT": "BTN",
  "BO": "BOL",
  "BA": "BIH",
  "BW": "BWA",
  "BR": "BRA",
  "IO": "IOT",
  "BN": "BRN",
  "BG": "BGR",
  "BF": "BFA",
  "BI": "BDI",
  "KH": "KHM",
  "CM": "CMR",
  "CA": "CAN",
  "CV": "CPV",
  "KY": "CYM",
  "CF": "CAF",
  "TD": "TCD",
  "CL": "CHL",
  "CN": "CHN",
  "CX": "CXR",
  "CC": "CCK",
  "CO": "COL",
  "KM": "COM",
  "CG": "COG",
  "CD": "COD",
  "CK": "COK",
  "CR": "CRI",
  "CI": "CIV",
  "HR": "HRV",
  "CU": "CUB",
  "CY": "CYP",
  "CZ": "CZE",
  "DK": "DNK",
  "DJ": "DJI",
  "DM": "DMA",
  "DO": "DOM",
  "EC": "ECU",
  "EG": "EGY",
  "SV": "SLV",
  "GQ": "GNQ",
  "ER": "ERI",
  "EE": "EST",
  "SZ": "SWZ",
  "ET": "ETH",
  "FK": "FLK",
  "FO": "FRO",
  "FJ": "FJI",
  "FI": "FIN",
  "FR": "FRA",
  "GF": "GUF",
  "PF": "PYF",
  "TF": "ATF",
  "GA": "GAB",
  "GM": "GMB",
  "GE": "GEO",
  "DE": "DEU",
  "GH": "GHA",
  "GI": "GIB",
  "GR": "GRC",
  "GL": "GRL",
  "GD": "GRD",
  "GP": "GLP",
  "GU": "GUM",
  "GT": "GTM",
  "GG": "GGY",
  "GN": "GIN",
  "GW": "GNB",
  "GY": "GUY",
  "HT": "HTI",
  "HN": "HND",
  "HK": "HKG",
  "HU": "HUN",
  "IS": "ISL",
  "IN": "IND",
  "ID": "IDN",
  "IR": "IRN",
  "IQ": "IRQ",
  "IE": "IRL",
  "IM": "IMN",
  "IL": "ISR",
  "IT": "ITA",
  "JM": "JAM",
  "JP": "JPN",
  "JE": "JEY",
  "JO": "JOR",
  "KZ": "KAZ",
  "KE": "KEN",
  "KI": "KIR",
  "KP": "PRK",
  "KR": "KOR",
  "KW": "KWT",
  "KG": "KGZ",
  "LA": "LAO",
  "LV": "LVA",
  "LB": "LBN",
  "LS": "LSO",
  "LR": "LBR",
  "LY": "LBY",
  "LI": "LIE",
  "LT": "LTU",
  "LU": "LUX",
  "MO": "MAC",
  "MG": "MDG",
  "MW": "MWI",
  "MY": "MYS",
  "MV": "MDV",
  "ML": "MLI",
  "MT": "MLT",
  "MH": "MHL",
  "MQ": "MTQ",
  "MR": "MRT",
  "MU": "MUS",
  "YT": "MYT",
  "MX": "MEX",
  "FM": "FSM",
  "MD": "MDA",
  "MC": "MCO",
  "MN": "MNG",
  "ME": "MNE",
  "MS": "MSR",
  "MA": "MAR",
  "MZ": "MOZ",
  "MM": "MMR",
  "NA": "NAM",
  "NR": "NRU",
  "NP": "NPL",
  "NL": "NLD",
  "NC": "NCL",
  "NZ": "NZL",
  "NI": "NIC",
  "NE": "NER",
  "NG": "NGA",
  "NU": "NIU",
  "NF": "NFK",
  "MK": "MKD",
  "MP": "MNP",
  "NO": "NOR",
  "OM": "OMN",
  "PK": "PAK",
  "PW": "PLW",
  "PS": "PSE",
  "PA": "PAN",
  "PG": "PNG",
  "PY": "PRY",
  "PE": "PER",
  "PH": "PHL",
  "PN": "PCN",
  "PL": "POL",
  "PT": "PRT",
  "PR": "PRI",
  "QA": "QAT",
  "RE": "REU",
  "RO": "ROU",
  "RU": "RUS",
  "RW": "RWA",
  "BL": "BLM",
  "SH": "SHN",
  "KN": "KNA",
  "LC": "LCA",
  "MF": "MAF",
  "PM": "SPM",
  "VC": "VCT",
  "WS": "WSM",
  "SM": "SMR",
  "ST": "STP",
  "SA": "SAU",
  "SN": "SEN",
  "RS": "SRB",
  "SC": "SYC",
  "SL": "SLE",
  "SG": "SGP",
  "SX": "SXM",
  "SK": "SVK",
  "SI": "SVN",
  "SB": "SLB",
  "SO": "SOM",
  "ZA": "ZAF",
  "GS": "SGS",
  "SS": "SSD",
  "ES": "ESP",
  "LK": "LKA",
  "SD": "SDN",
  "SR": "SUR",
  "SE": "SWE",
  "CH": "CHE",
  "SY": "SYR",
  "TW": "TWN",
  "TJ": "TJK",
  "TZ": "TZA",
  "TH": "THA",
  "TL": "TLS",
  "TG": "TGO",
  "TK": "TKL",
  "TO": "TON",
  "TT": "TTO",
  "TN": "TUN",
  "TR": "TUR",
  "TM": "TKM",
  "TC": "TCA",
  "TV": "TUV",
  "UG": "UGA",
  "UA": "UKR",
  "AE": "ARE",
  "GB": "GBR",
  "US": "USA",
  "UY": "URY",
  "UZ": "UZB",
  "VU": "VUT",
  "VE": "VEN",
  "VN": "VNM",
  "VG": "VGB",
  "VI": "VIR",
  "YE": "YEM",
  "ZM": "ZMB",
  "ZW": "ZWE",
  "XK": "XKX"
}
