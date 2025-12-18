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
