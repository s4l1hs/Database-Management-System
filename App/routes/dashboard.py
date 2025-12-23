from flask import Blueprint, render_template, session
from App.db import get_db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    is_admin = session.get("team_no") == 1

    db = get_db()
    cur = db.cursor(dictionary=True)

    coverage = {
        "countries": 0,
        "global_min_year": None,
        "global_max_year": None,
        "completeness_pct": None,
        "indicators": {
            "ghg": 0,
            "health": 0,
            "energy": 0,
            "freshwater": 0,
            "sustainability": 0,
        },
        "domains": {},
    }

    try:
        # Total country count
        cur.execute("SELECT COUNT(*) AS cnt FROM countries")
        row = cur.fetchone()
        coverage["countries"] = row["cnt"] if row and row.get("cnt") is not None else 0

        domains = [
            {
                "name": "health",
                "fact_table": "health_system",
                "detail_table": "health_indicator_details",
                "indicator_pk": "health_indicator_id",
                "value_column": "indicator_value",
            },
            {
                "name": "energy",
                "fact_table": "energy_data",
                "detail_table": "energy_indicator_details",
                "indicator_pk": "energy_indicator_id",
                "value_column": "indicator_value",
            },
            {
                "name": "freshwater",
                "fact_table": "freshwater_data",
                "detail_table": "freshwater_indicator_details",
                "indicator_pk": "freshwater_indicator_id",
                "value_column": "indicator_value",
            },
            {
                "name": "ghg",
                "fact_table": "greenhouse_emissions",
                "detail_table": "ghg_indicator_details",
                "indicator_pk": "ghg_indicator_id",
                "value_column": "indicator_value",
            },
            {
                "name": "sustainability",
                "fact_table": "sustainability_data",
                "detail_table": "sustainability_indicator_details",
                "indicator_pk": "sus_indicator_id",
                "value_column": "indicator_value",
            },
        ]

        global_min_year = None
        global_max_year = None
        total_expected = 0
        total_actual = 0
        countries_count = coverage["countries"] or 0

        for d in domains:
            # Indicator count per domain
            try:
                cur.execute(
                    f"SELECT COUNT(*) AS cnt FROM {d['detail_table']}"
                )
                row = cur.fetchone()
                ind_cnt = row["cnt"] if row and row.get("cnt") is not None else 0
            except Exception:
                ind_cnt = 0
            coverage["indicators"][d["name"]] = ind_cnt

            # Year range, country coverage and actual record count (non-null values)
            try:
                cur.execute(
                    f"""
                    SELECT
                        MIN(year) AS min_year,
                        MAX(year) AS max_year,
                        COUNT(*) AS records,
                        COUNT(DISTINCT country_id) AS countries_with_data
                    FROM {d['fact_table']}
                    WHERE {d['value_column']} IS NOT NULL
                    """
                )
                stats = cur.fetchone() or {}
            except Exception:
                stats = {}

            min_year = stats.get("min_year")
            max_year = stats.get("max_year")
            records = stats.get("records") or 0
            domain_countries = stats.get("countries_with_data") or 0

            domain_coverage_pct = None
            if countries_count > 0 and domain_countries >= 0:
                domain_coverage_pct = round(
                    (float(domain_countries) / float(countries_count)) * 100.0, 1
                )

            coverage["domains"][d["name"]] = {
                "indicators": ind_cnt,
                "min_year": min_year,
                "max_year": max_year,
                "country_coverage_pct": domain_coverage_pct,
            }

            if min_year is None or max_year is None or ind_cnt == 0 or countries_count == 0:
                continue

            if global_min_year is None or (min_year is not None and min_year < global_min_year):
                global_min_year = min_year
            if global_max_year is None or (max_year is not None and max_year > global_max_year):
                global_max_year = max_year

            year_span = max_year - min_year + 1
            if year_span <= 0:
                continue

            expected = countries_count * year_span * ind_cnt
            total_expected += expected
            total_actual += records

        coverage["global_min_year"] = global_min_year
        coverage["global_max_year"] = global_max_year

        if total_expected > 0 and total_actual >= 0:
            coverage["completeness_pct"] = round(
                (float(total_actual) / float(total_expected)) * 100.0, 1
            )
    finally:
        cur.close()

    # Domain shortcuts for hero section (single source of truth, navbar order)
    domains = [
        {
            "key": "overview",
            "label": "Overview",
            "endpoint": "dashboard.dashboard",
            "icon": "fa-gauge-high",
            "coverage_key": None,
        },
        {
            "key": "countries",
            "label": "Countries",
            "endpoint": "countries.list_countries",
            "icon": "fa-map",
            "coverage_key": None,
        },
        {
            "key": "health",
            "label": "Health",
            "endpoint": "health.list_health",
            "icon": "fa-heart-pulse",
            "coverage_key": "health",
        },
        {
            "key": "ghg",
            "label": "GHG Emissions",
            "endpoint": "ghg.list_ghg",
            "icon": "fa-smog",
            "coverage_key": "ghg",
        },
        {
            "key": "energy",
            "label": "Energy",
            "endpoint": "energy.list_energy",
            "icon": "fa-bolt",
            "coverage_key": "energy",
        },
        {
            "key": "freshwater",
            "label": "Freshwater",
            "endpoint": "freshwater.list_freshwater",
            "icon": "fa-droplet",
            "coverage_key": "freshwater",
        },
        {
            "key": "sustainability",
            "label": "Sustainability",
            "endpoint": "sustainability.list_sustainability",
            "icon": "fa-leaf",
            "coverage_key": "sustainability",
        },
    ]

    domains_meta = []
    for d in domains:
        cov_key = d.get("coverage_key")
        enabled = True
        if cov_key:
            dom_cov = (coverage.get("domains") or {}).get(cov_key) or {}
            ind_cnt = dom_cov.get("indicators") or 0
            enabled = ind_cnt > 0
        d_copy = dict(d)
        d_copy["enabled"] = enabled
        domains_meta.append(d_copy)

    return render_template(
        "dashboard.html",
        is_admin=is_admin,
        coverage=coverage,
        domain_shortcuts=domains_meta,
    )
