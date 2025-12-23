import mysql.connector
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, abort
)
from App.db import get_db
from App.routes.login import admin_required, editor_required

energy_bp = Blueprint("energy", __name__, url_prefix="/energy")

# --- HELPER: Load Lists for Dropdowns ---
def _load_countries_and_indicators():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # 1. Get Countries
    cur.execute("SELECT country_id, country_name FROM countries ORDER BY country_name")
    countries = cur.fetchall()
    
    # 2. Get Energy Indicators 
    cur.execute("""
        SELECT energy_indicator_id, indicator_name, measurement_unit 
        FROM energy_indicator_details 
        ORDER BY indicator_name
    """)
    indicators = cur.fetchall()
    
    return countries, indicators

# --- 1. READ (LIST + FILTER) ---
@energy_bp.route("/", methods=["GET"])
def list_energy():
    country_name = request.args.get("country", type=str)
    year_min = request.args.get("year_min", type=int)
    year_max = request.args.get("year_max", type=int)
    sort_by = request.args.get("sort", default="country", type=str)
    sort_order = request.args.get("order", default="asc", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = 50

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Build WHERE clause
    where_clauses = []
    params = []

    if country_name:
        where_clauses.append("c.country_name LIKE %s")
        params.append(f"%{country_name}%")

    if year_min:
        where_clauses.append("e.year >= %s")
        params.append(year_min)

    if year_max:
        where_clauses.append("e.year <= %s")
        params.append(year_max)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get summary rows grouped by (country, year)
    query = f"""
        SELECT DISTINCT
            c.country_id,
            c.country_name,
            c.country_code,
            c.region,
            e.year
        FROM countries c
        INNER JOIN energy_data e ON c.country_id = e.country_id
        WHERE {where_sql}
    """

    # Sorting
    sort_map = {
        "country": "country_name",
        "year": "year",
        "region": "region"
    }
    sort_column = sort_map.get(sort_by, "country_name")
    order = "ASC" if sort_order == "asc" else "DESC"
    query += f" ORDER BY {sort_column} {order}"

    # Get total count for pagination
    count_query = f"""
        SELECT COUNT(DISTINCT c.country_id, e.year) as total
        FROM countries c
        INNER JOIN energy_data e ON c.country_id = e.country_id
        WHERE {where_sql}
    """
    cur.execute(count_query, params)
    total_count = cur.fetchone()['total']
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    # Apply pagination
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"

    cur.execute(query, params)
    summary_rows = cur.fetchall()

    # Get detailed data for each country-year pair
    detailed_data = {}
    time_series_data = {}  # For chart visualization
    
    # Get unique country IDs from summary rows
    country_ids = list(set(row['country_id'] for row in summary_rows))
    
    # Prepare time_series_data for all countries (same structure as GHG)
    for country_id in country_ids:
        # Get all available indicators from database
        cur.execute("""
            SELECT energy_indicator_id, indicator_name, measurement_unit
            FROM energy_indicator_details
            ORDER BY energy_indicator_id
        """)
        all_indicators = cur.fetchall()
        indicator_map = {row['energy_indicator_id']: {'name': row['indicator_name'], 'unit': row['measurement_unit'] or ''} for row in all_indicators}
        
        # Get all years for this country
        cur.execute("""
            SELECT DISTINCT year
            FROM energy_data
            WHERE country_id = %s
            ORDER BY year ASC
        """, (country_id,))
        all_years = [row['year'] for row in cur.fetchall()]
        
        # Build time-series data for each indicator dynamically
        country_ts_by_indicator = {}
        for indicator_id, indicator_info in indicator_map.items():
            cur.execute("""
                SELECT year, indicator_value
                FROM energy_data
                WHERE country_id = %s AND energy_indicator_id = %s AND indicator_value IS NOT NULL
                ORDER BY year ASC
            """, (country_id, indicator_id))
            indicator_data = {row['year']: float(row['indicator_value']) for row in cur.fetchall()}
            
            # Build complete time-series with all years (null for missing years)
            country_ts_by_indicator[indicator_id] = [
                {
                    'year': year,
                    'value': indicator_data.get(year)
                }
                for year in all_years
            ]
        
        # Get region for region average calculation
        cur.execute("SELECT region FROM countries WHERE country_id = %s", (country_id,))
        region_result = cur.fetchone()
        region_name = region_result['region'] if region_result else None
        
        # Get region average time-series for all indicators if region exists
        region_avg_by_indicator = {}
        if region_name:
            for indicator_id in indicator_map.keys():
                cur.execute("""
                    SELECT year, AVG(indicator_value) as avg_value
                    FROM energy_data e
                    INNER JOIN countries c ON c.country_id = e.country_id
                    WHERE c.region = %s AND e.energy_indicator_id = %s AND e.indicator_value IS NOT NULL
                    GROUP BY year
                    ORDER BY year ASC
                """, (region_name, indicator_id))
                region_data = {row['year']: float(row['avg_value']) for row in cur.fetchall()}
                
                region_avg_by_indicator[indicator_id] = [
                    {
                        'year': year,
                        'value': region_data.get(year)
                    }
                    for year in all_years
                ]
        
        time_series_data[country_id] = {
            'indicators': indicator_map,
            'country_data': country_ts_by_indicator,
            'region_avg': region_avg_by_indicator,
            'region': region_name,
            'years': all_years
        }
    
    # Get detailed data for each country-year pair
    for row in summary_rows:
        country_id = row['country_id']
        year = row['year']
        key = f"{country_id}-{year}"

        # Get all indicators for this country-year pair
        detail_query = """
            SELECT 
                e.data_id,
                e.energy_indicator_id,
                e.indicator_value,
                e.data_source,
                ind.indicator_name,
                ind.measurement_unit
            FROM energy_data e
            INNER JOIN energy_indicator_details ind ON e.energy_indicator_id = ind.energy_indicator_id
            WHERE e.country_id = %s AND e.year = %s
            ORDER BY ind.indicator_name
        """
        cur.execute(detail_query, (country_id, year))
        detailed_data[key] = cur.fetchall()

    # Get countries and indicators for dropdowns
    cur.execute("SELECT country_id, country_name, country_code FROM countries ORDER BY country_name")
    countries = cur.fetchall()

    cur.execute("""
        SELECT energy_indicator_id, indicator_name, measurement_unit 
        FROM energy_indicator_details 
        ORDER BY indicator_name
    """)
    indicators = cur.fetchall()

    # Calculate global average by year for all indicators (for Trend Explorer)
    global_avg_by_year = {}
    for indicator in indicators:
        indicator_id = indicator['energy_indicator_id']
        cur.execute("""
            SELECT 
                year,
                AVG(indicator_value) as avg_value,
                COUNT(DISTINCT country_id) as country_count
            FROM energy_data
            WHERE energy_indicator_id = %s 
            AND indicator_value IS NOT NULL
            GROUP BY year
            ORDER BY year ASC
        """, (indicator_id,))
        global_avg_by_year[indicator_id] = [
            {
                'year': row['year'],
                'avg_value': float(row['avg_value']),
                'country_count': row['country_count']
            }
            for row in cur.fetchall()
        ]

    return render_template(
        "energy_list.html",
        summary_rows=summary_rows,
        detailed_data=detailed_data,
        time_series_data=time_series_data,
        global_avg_by_year=global_avg_by_year,
        current_country=country_name,
        current_year_min=year_min,
        current_year_max=year_max,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        countries=countries,
        indicators=indicators
    )

# --- 2. CREATE (ADD) ---
@energy_bp.route("/add", methods=["GET", "POST"])
@editor_required
def add_energy():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        try:
            # Capture form data
            c_id = request.form.get("country_id", type=int)
            i_id = request.form.get("energy_indicator_id", type=int)
            year = request.form.get("year", type=int)
            val = request.form.get("indicator_value", type=float)
            note = request.form.get("data_source")

            # Insert Data
            insert_sql = """
                INSERT INTO energy_data 
                (country_id, energy_indicator_id, indicator_value, year, data_source)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(insert_sql, (c_id, i_id, val, year, note))
            new_id = cur.lastrowid # Get the ID of the row we just created
            
            # --- AUDIT LOG ---
            current_student_id = session.get("student_id")
            if current_student_id:
                audit_sql = """
                    INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(audit_sql, (current_student_id, "CREATE", "energy_data", new_id))
            
            db.commit()
            flash("Record added successfully.", "success")
            return redirect(url_for("energy.list_energy"))

        except mysql.connector.IntegrityError as e:
            db.rollback()
            if e.errno == 1062: # Duplicate entry error code
                flash("This country + indicator + year combination already exists!", "danger")
            else:
                flash(f"Database Integrity Error: {e}", "danger")
            return redirect(url_for("energy.add_energy"))
            
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("energy.add_energy"))

    # GET request: Show form
    countries, indicators = _load_countries_and_indicators()
    
    
    return render_template(
        "energy_form.html", 
        countries=countries, 
        indicators=indicators, 
        action="Add", 
        record=None
    )

# --- 3. UPDATE (EDIT) ---
@energy_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@editor_required
def edit_energy(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # Fetch existing record
    cur.execute("SELECT * FROM energy_data WHERE data_id = %s", (id,))
    record = cur.fetchone()

    if not record:
        abort(404)

    if request.method == "POST":
        try:
            val = request.form.get("indicator_value", type=float)
            year = request.form.get("year", type=int)
            note = request.form.get("data_source")

            update_sql = """
                UPDATE energy_data 
                SET indicator_value = %s, year = %s, data_source = %s
                WHERE data_id = %s
            """
            cur = db.cursor() # reset cursor without dictionary for standard execution
            cur.execute(update_sql, (val, year, note, id))

            # --- AUDIT LOG ---
            current_student_id = session.get("student_id")
            if current_student_id:
                audit_sql = """
                    INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(audit_sql, (current_student_id, "UPDATE", "energy_data", id))
            
            db.commit()
            flash("Record updated successfully.", "success")
            return redirect(url_for("energy.list_energy"))

        except Exception as e:
            db.rollback()
            flash(f"Update Error: {e}", "danger")

    
    countries, indicators = _load_countries_and_indicators()
    return render_template(
        "energy_form.html", 
        record=record,
        countries=countries,
        indicators=indicators,
        action="Edit"
    )

# --- 4. DELETE ---
@energy_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_energy(id):
    db = get_db()
    cur = db.cursor()

    try:
        # --- AUDIT LOG (Before Delete) ---
        current_student_id = session.get("student_id")
        if current_student_id:
            audit_sql = """
                INSERT INTO audit_logs (student_id, action_type, table_name, record_id)
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(audit_sql, (current_student_id, "DELETE", "energy_data", id))

        # Perform Delete
        cur.execute("DELETE FROM energy_data WHERE data_id = %s", (id,))
        db.commit()
        
        flash("Record deleted successfully.", "success")
    except Exception as e:
        db.rollback()
        flash(f"Delete Error: {e}", "danger")

    return redirect(url_for("energy.list_energy"))
    
