from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
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


# ---------- LIST (Summary View) ----------
@ghg_bp.route("/", methods=["GET"])
def list_ghg():
    country_name = request.args.get("country", type=str)
    year_min = request.args.get("year_min", type=int)
    year_max = request.args.get("year_max", type=int)
    latest_year_only = request.args.get("latest_year_only", type=str) == "true"
    sort_by = request.args.get("sort", default="country", type=str)
    sort_order = request.args.get("order", default="asc", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = 50

    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=True)

    try:
        # Build WHERE clause
        where_clauses = []
        params = []

        if country_name:
            where_clauses.append("c.country_name LIKE %s")
            params.append(f"%{country_name}%")

        if year_min:
            where_clauses.append("g.year >= %s")
            params.append(year_min)

        if year_max:
            where_clauses.append("g.year <= %s")
            params.append(year_max)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # If latest_year_only is enabled, filter to show only the latest year per country
        if latest_year_only:
            # Add a condition to match only the latest year for each country
            # This uses a correlated subquery to find the max year per country
            latest_year_condition = """
                AND g.year = (
                    SELECT MAX(g2.year)
                    FROM greenhouse_emissions g2
                    WHERE g2.country_id = g.country_id
                )
            """
            where_sql = f"{where_sql} {latest_year_condition}"

        # Aggregate query: Get summary data grouped by (country, year)
        # This ensures exactly one row per unique (country, year) combination
        # Using a subquery approach to ensure proper aggregation
        # Indicator IDs: 1=Total GHG, 5=CO2 Total, 6=CO2 per capita
        query = f"""
            SELECT 
                country_id,
                country_name,
                country_code,
                region,
                year,
                CAST(MAX(CASE WHEN ghg_indicator_id = 1 THEN indicator_value END) AS UNSIGNED) AS total_ghg,
                CAST(MAX(CASE WHEN ghg_indicator_id = 5 THEN indicator_value END) AS UNSIGNED) AS co2_total,
                CAST(MAX(CASE WHEN ghg_indicator_id = 6 THEN indicator_value END) AS DECIMAL(10,2)) AS co2_per_capita
            FROM (
                SELECT DISTINCT
                    c.country_id,
                    c.country_name,
                    c.country_code,
                    c.region,
                    g.year,
                    g.ghg_indicator_id,
                    g.indicator_value
                FROM countries c
                INNER JOIN greenhouse_emissions g ON c.country_id = g.country_id
                WHERE {where_sql}
            ) AS emission_data
            GROUP BY country_id, country_name, country_code, region, year
        """
        

        # Sorting with NULL handling - NULL values always at bottom
        # Only allow sorting on meaningful numeric columns
        sortable_numeric_columns = ["total_ghg", "co2_total", "co2_per_capita", "trend"]
        sort_map = {
            "country": "country_name",
            "year": "year",
            "region": "region",
            "total_ghg": "total_ghg",
            "co2_total": "co2_total",
            "co2_per_capita": "co2_per_capita",
            "trend": "trend_value"  # Will be calculated in Python after trend computation
        }
        
        # For numeric columns, handle NULLs properly - NULL values always at bottom
        if sort_by in ["total_ghg", "co2_total", "co2_per_capita"]:
            sort_column = sort_map.get(sort_by)
            order = "ASC" if sort_order == "asc" else "DESC"
            # NULL values always at bottom: IS NULL returns 1 for NULL, 0 for non-NULL
            # So NULLs (1) come after non-NULLs (0) in ascending order
            query += f" ORDER BY {sort_column} IS NULL, {sort_column} {order}"
        elif sort_by == "trend":
            # Trend sorting will be done in Python after calculation
            query += " ORDER BY country_name ASC"
        else:
            # Non-numeric columns: country, year, region
            sort_column = sort_map.get(sort_by, "country_name")
            order = "ASC" if sort_order == "asc" else "DESC"
            # Handle NULLs for region and country (though they shouldn't be NULL, ensure consistency)
            if sort_by in ["region", "country"]:
                query += f" ORDER BY {sort_column} IS NULL, {sort_column} {order}"
            else:
                query += f" ORDER BY {sort_column} {order}"

        # Get total count for pagination - count unique (country, year) pairs
        # Use the same grouping logic as the main query
        count_query = f"""
            SELECT COUNT(*) as total
            FROM (
                SELECT 
                    c.country_id,
                    g.year
                FROM countries c
                INNER JOIN greenhouse_emissions g ON c.country_id = g.country_id
                WHERE {where_sql}
                GROUP BY c.country_id, g.year
            ) as unique_pairs
        """
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        # Apply pagination
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        cursor.execute(query, params)
        raw_rows = cursor.fetchall()

        # Enforce strict uniqueness: Use dictionary to ensure one row per (country, year)
        # This is a safety measure in case GROUP BY doesn't work as expected
        unique_summary_dict = {}
        for row in raw_rows:
            pair_key = (row['country_id'], row['year'])
            if pair_key not in unique_summary_dict:
                unique_summary_dict[pair_key] = row
            else:
                # If duplicate found, merge indicator values (shouldn't happen with proper GROUP BY)
                existing = unique_summary_dict[pair_key]
                if row['total_ghg'] is not None and existing['total_ghg'] is None:
                    existing['total_ghg'] = row['total_ghg']
                if row['co2_total'] is not None and existing['co2_total'] is None:
                    existing['co2_total'] = row['co2_total']
                if row['co2_per_capita'] is not None and existing['co2_per_capita'] is None:
                    existing['co2_per_capita'] = row['co2_per_capita']
        
        summary_rows = list(unique_summary_dict.values())
        
        # Calculate trends for each country using FULL historical dataset (ignoring filters)
        # Get all unique countries from summary rows (visible countries)
        country_ids = list(set(row['country_id'] for row in summary_rows))
        trend_data = {}
        
        if country_ids:
            # Build placeholders for IN clause
            placeholders = ','.join(['%s'] * len(country_ids))
            
            # For each indicator, get earliest and latest values per country from FULL dataset
            # This ignores year_min, year_max, and latest_year_only filters
            for indicator_id, indicator_key in [(1, 'total_ghg'), (5, 'co2_total'), (6, 'co2_per_capita')]:
                # Get min/max years for each country-indicator combination from FULL dataset
                year_range_query = f"""
                    SELECT country_id, MIN(year) as min_year, MAX(year) as max_year
                    FROM greenhouse_emissions
                    WHERE country_id IN ({placeholders}) AND ghg_indicator_id = %s
                    GROUP BY country_id
                """
                cursor.execute(year_range_query, country_ids + [indicator_id])
                year_ranges = {row['country_id']: (row['min_year'], row['max_year']) for row in cursor.fetchall()}
                
                # Get values for earliest and latest years from FULL dataset
                for country_id, (min_year, max_year) in year_ranges.items():
                    if country_id not in trend_data:
                        trend_data[country_id] = {}
                    
                    # Get earliest value from FULL dataset
                    earliest_query = """
                        SELECT indicator_value FROM greenhouse_emissions
                        WHERE country_id = %s AND ghg_indicator_id = %s AND year = %s
                        LIMIT 1
                    """
                    cursor.execute(earliest_query, (country_id, indicator_id, min_year))
                    earliest_result = cursor.fetchone()
                    earliest_value = earliest_result['indicator_value'] if earliest_result else None
                    
                    # Get latest value from FULL dataset
                    latest_query = """
                        SELECT indicator_value FROM greenhouse_emissions
                        WHERE country_id = %s AND ghg_indicator_id = %s AND year = %s
                        LIMIT 1
                    """
                    cursor.execute(latest_query, (country_id, indicator_id, max_year))
                    latest_result = cursor.fetchone()
                    latest_value = latest_result['indicator_value'] if latest_result else None
                    
                    trend_data[country_id][indicator_key] = {
                        'earliest': float(earliest_value) if earliest_value is not None else None,
                        'latest': float(latest_value) if latest_value is not None else None,
                        'earliest_year': min_year,
                        'latest_year': max_year
                    }
        
        # Find the latest year for each country from FULL dataset (not filtered rows)
        # This ensures trends are shown correctly even when latest_year_only filter is active
        country_latest_years_full = {}
        if country_ids:
            placeholders = ','.join(['%s'] * len(country_ids))
            cursor.execute(f"""
                SELECT country_id, MAX(year) as max_year
                FROM greenhouse_emissions
                WHERE country_id IN ({placeholders})
                GROUP BY country_id
            """, country_ids)
            country_latest_years_full = {row['country_id']: row['max_year'] for row in cursor.fetchall()}
        
        # Also get earliest years from FULL dataset for is_earliest_year flag
        country_earliest_years_full = {}
        if country_ids:
            placeholders = ','.join(['%s'] * len(country_ids))
            cursor.execute(f"""
                SELECT country_id, MIN(year) as min_year
                FROM greenhouse_emissions
                WHERE country_id IN ({placeholders})
                GROUP BY country_id
            """, country_ids)
            country_earliest_years_full = {row['country_id']: row['min_year'] for row in cursor.fetchall()}
        
        # Calculate trend values and add to summary rows
        # Trend is only shown for the latest year per country (from FULL dataset)
        for row in summary_rows:
            country_id = row['country_id']
            year = row['year']
            # Use full dataset latest year, not filtered rows
            is_latest_year = country_latest_years_full.get(country_id) == year
            
            trends = {}
            show_trend = False
            
            # Only calculate and show trend for the latest year of each country
            if is_latest_year and country_id in trend_data:
                country_trends = trend_data[country_id]
                
                # Calculate trend for CO2 per capita (primary metric for trend display)
                if 'co2_per_capita' in country_trends:
                    t = country_trends['co2_per_capita']
                    # Check if we have valid previous data (earliest year must exist and be different from latest)
                    if t['earliest'] is not None and t['latest'] is not None and t['earliest_year'] is not None and t['earliest_year'] < t['latest_year']:
                        earliest_val = float(t['earliest'])
                        latest_val = float(t['latest'])
                        trends['co2_per_capita'] = {
                            'change': latest_val - earliest_val,
                            'percent': ((latest_val - earliest_val) / earliest_val * 100) if earliest_val != 0 else None,
                            'earliest_year': t['earliest_year'],
                            'latest_year': t['latest_year']
                        }
                        show_trend = True
                    else:
                        trends['co2_per_capita'] = None
                else:
                    trends['co2_per_capita'] = None
            else:
                trends = {'co2_per_capita': None}
            
            row['trends'] = trends
            row['show_trend'] = show_trend
            row['is_latest_year'] = is_latest_year
            row['is_earliest_year'] = False  # Will be set below
            
            # Calculate primary trend value for sorting (use CO2 per capita)
            if trends['co2_per_capita'] is not None:
                row['trend_value'] = trends['co2_per_capita']['change']
            else:
                row['trend_value'] = None
        
        # Mark earliest year rows using FULL dataset (not filtered)
        for row in summary_rows:
            country_id = row['country_id']
            year = row['year']
            # Use full dataset earliest year
            row['is_earliest_year'] = country_earliest_years_full.get(country_id) == year
        
        # Get unit symbols for summary indicators (1=Total GHG, 5=CO2 Total, 6=CO2 per capita)
        cursor.execute("""
            SELECT ghg_indicator_id, unit_symbol
            FROM ghg_indicator_details
            WHERE ghg_indicator_id IN (1, 5, 6)
        """)
        unit_symbols = {row['ghg_indicator_id']: row['unit_symbol'] for row in cursor.fetchall()}
        
        # Group rows by country for accordion-style display
        # Organize: {country_id: {country_info, years: [sorted rows]}}
        countries_grouped = {}
        for row in summary_rows:
            country_id = row['country_id']
            if country_id not in countries_grouped:
                countries_grouped[country_id] = {
                    'country_id': country_id,
                    'country_name': row['country_name'],
                    'country_code': row['country_code'],
                    'region': row['region'],
                    'years': []
                }
            countries_grouped[country_id]['years'].append(row)
        
        # Sort years within each country (ascending)
        for country_id in countries_grouped:
            countries_grouped[country_id]['years'].sort(key=lambda x: x['year'])
        
        # Get region averages per year for comparison (B2)
        region_avg_by_year = {}
        if summary_rows:
            # Get unique regions and years
            regions = list(set(row['region'] for row in summary_rows if row['region']))
            years = list(set(row['year'] for row in summary_rows))
            
            if regions and years:
                placeholders_years = ','.join(['%s'] * len(years))
                for region in regions:
                    cursor.execute(f"""
                        SELECT year, AVG(indicator_value) as avg_value
                        FROM greenhouse_emissions g
                        INNER JOIN countries c ON c.country_id = g.country_id
                        WHERE c.region = %s 
                        AND g.ghg_indicator_id = 6 
                        AND g.indicator_value IS NOT NULL
                        AND g.year IN ({placeholders_years})
                        GROUP BY year
                    """, [region] + years)
                    region_avg_by_year[region] = {row['year']: float(row['avg_value']) for row in cursor.fetchall()}
        
        # Calculate global average CO₂ per capita by year (for global trend chart)
        # Use indicator ID 6 (CO₂ per capita)
        # Include ALL available reporting years, regardless of country count
        global_avg_by_year = []
        cursor.execute("""
            SELECT 
                year,
                AVG(indicator_value) as avg_value,
                COUNT(DISTINCT country_id) as country_count
            FROM greenhouse_emissions
            WHERE ghg_indicator_id = 6 
            AND indicator_value IS NOT NULL
            GROUP BY year
            ORDER BY year ASC
        """)
        global_avg_by_year = [
            {
                'year': row['year'],
                'avg_value': float(row['avg_value']),
                'country_count': row['country_count']
            }
            for row in cursor.fetchall()
        ]
        
        # Calculate top risers/decliners (B1) - percentage-based changes in CO2 per capita
        top_risers = []
        top_decliners = []
        if trend_data:
            risers_decliners = []
            for country_id, trends in trend_data.items():
                if 'co2_per_capita' in trends and trends['co2_per_capita']:
                    t = trends['co2_per_capita']
                    if t['earliest'] is not None and t['latest'] is not None and t['earliest_year'] < t['latest_year']:
                        percent_change = ((t['latest'] - t['earliest']) / t['earliest'] * 100) if t['earliest'] != 0 else None
                        if percent_change is not None:
                            # Get country name
                            country_name = next((row['country_name'] for row in summary_rows if row['country_id'] == country_id), 'Unknown')
                            risers_decliners.append({
                                'country_id': country_id,
                                'country_name': country_name,
                                'percent_change': percent_change,
                                'earliest_year': t['earliest_year'],
                                'latest_year': t['latest_year']
                            })
            
            # Sort and get top 5
            risers_decliners.sort(key=lambda x: x['percent_change'], reverse=True)
            top_risers = risers_decliners[:5]
            top_decliners = sorted(risers_decliners[-5:], key=lambda x: x['percent_change'])
        
        # Calculate data coverage per country (D2)
        country_coverage = {}
        for country_id in countries_grouped:
            years_list = countries_grouped[country_id]['years']
            total_years = len(years_list)
            # Count years with data in the filtered range
            if year_min or year_max:
                filtered_years = [y for y in years_list if (not year_min or y['year'] >= year_min) and (not year_max or y['year'] <= year_max)]
                total_years = len(filtered_years)
            country_coverage[country_id] = {
                'reported': total_years,
                'total': total_years  # Could be enhanced to show total possible years
            }
        
        # Apply sorting to country groups
        # Convert grouped dict to list for sorting
        countries_list = list(countries_grouped.values())
        
        if sort_by == "trend":
            # Sort by trend value of latest year
            countries_list.sort(
                key=lambda c: (
                    next((y['trend_value'] is None for y in c['years'] if y.get('is_latest_year')), True),
                    next((y['trend_value'] for y in c['years'] if y.get('is_latest_year')), 0)
                ),
                reverse=(sort_order == "desc")
            )
        elif sort_by == "country":
            countries_list.sort(
                key=lambda c: c['country_name'].lower(),
                reverse=(sort_order == "desc")
            )
        elif sort_by == "region":
            countries_list.sort(
                key=lambda c: (c['region'] or '').lower(),
                reverse=(sort_order == "desc")
            )
        elif sort_by in ["co2_per_capita", "co2_total", "total_ghg"]:
            # Sort by latest year value
            def get_latest_value(c, field):
                latest_year = max(c['years'], key=lambda y: y['year'])
                return latest_year.get(field) if latest_year.get(field) is not None else float('-inf')
            
            countries_list.sort(
                key=lambda c: (
                    get_latest_value(c, sort_by) == float('-inf'),
                    get_latest_value(c, sort_by)
                ),
                reverse=(sort_order == "desc")
            )
        else:  # year or default
            countries_list.sort(
                key=lambda c: max(y['year'] for y in c['years']),
                reverse=(sort_order == "desc")
            )

        # For each summary row, get detailed indicators
        detailed_data = {}
        time_series_data = {}  # For chart visualization
        
        # Get total number of indicators for coverage calculation
        cursor.execute("SELECT COUNT(*) as total FROM ghg_indicator_details")
        total_indicators = cursor.fetchone()['total']
        
        for row in summary_rows:
            country_id = row['country_id']
            year = row['year']
            key = f"{country_id}-{year}"

            # Get all indicators for this country-year pair
            detail_query = """
                SELECT 
                    g.row_id,
                    g.ghg_indicator_id,
                    g.indicator_value,
                    g.share_of_total_pct,
                    g.uncertainty_pct,
                    g.source_notes,
                    i.indicator_name,
                    i.unit_symbol
                FROM greenhouse_emissions g
                INNER JOIN ghg_indicator_details i ON g.ghg_indicator_id = i.ghg_indicator_id
                WHERE g.country_id = %s AND g.year = %s
                ORDER BY g.ghg_indicator_id
            """
            cursor.execute(detail_query, (country_id, year))
            detailed_data[key] = cursor.fetchall()
            
            # Calculate data coverage: count indicators with valid data
            coverage_count = sum(1 for detail in detailed_data[key] if detail['indicator_value'] is not None)
            row['data_coverage'] = {
                'reported': coverage_count,
                'total': total_indicators
            }
            
            # Get time-series data for this country (all years)
            # Only fetch once per unique country_id
            # Returns metric-agnostic structure for ALL indicators dynamically
            if country_id not in time_series_data:
                # Get all available indicators from database
                cursor.execute("""
                    SELECT ghg_indicator_id, indicator_name, unit_symbol
                    FROM ghg_indicator_details
                    ORDER BY ghg_indicator_id
                """)
                all_indicators = cursor.fetchall()
                indicator_map = {row['ghg_indicator_id']: {'name': row['indicator_name'], 'unit': row['unit_symbol']} for row in all_indicators}
                
                # Get all years for this country
                cursor.execute("""
                    SELECT DISTINCT year
                    FROM greenhouse_emissions
                    WHERE country_id = %s
                    ORDER BY year ASC
                """, (country_id,))
                all_years = [row['year'] for row in cursor.fetchall()]
                
                # Build time-series data for each indicator dynamically
                country_ts_by_indicator = {}
                for indicator_id, indicator_info in indicator_map.items():
                    cursor.execute("""
                        SELECT year, indicator_value
                        FROM greenhouse_emissions
                        WHERE country_id = %s AND ghg_indicator_id = %s AND indicator_value IS NOT NULL
                        ORDER BY year ASC
                    """, (country_id, indicator_id))
                    indicator_data = {row['year']: row['indicator_value'] for row in cursor.fetchall()}
                    
                    # Build complete time-series with all years (null for missing years)
                    country_ts_by_indicator[indicator_id] = [
                        {
                            'year': year,
                            'value': indicator_data.get(year)
                        }
                        for year in all_years
                    ]
                
                # Get region for region average calculation
                cursor.execute("SELECT region FROM countries WHERE country_id = %s", (country_id,))
                region_result = cursor.fetchone()
                region_name = region_result['region'] if region_result else None
                
                # Get region average time-series for all indicators if region exists
                region_avg_by_indicator = {}
                if region_name:
                    for indicator_id in indicator_map.keys():
                        cursor.execute("""
                            SELECT year, AVG(indicator_value) as avg_value
                            FROM greenhouse_emissions g
                            INNER JOIN countries c ON c.country_id = g.country_id
                            WHERE c.region = %s AND g.ghg_indicator_id = %s AND g.indicator_value IS NOT NULL
                            GROUP BY year
                            ORDER BY year ASC
                        """, (region_name, indicator_id))
                        region_data = {row['year']: row['avg_value'] for row in cursor.fetchall()}
                        
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

    except MySQLError as e:
        flash(f"Database error: {e}", "danger")
        summary_rows = []
        countries_list = []
        detailed_data = {}
        time_series_data = {}
        unit_symbols = {1: 'kt CO₂-eq', 5: 'kt', 6: 't'}  # Default fallback
        region_avg_by_year = {}
        global_avg_by_year = []
        top_risers = []
        top_decliners = []
        country_coverage = {}
        total_pages = 0
    finally:
        cursor.close()

    return render_template(
        "ghg_list.html",
        countries_grouped=countries_list,  # Grouped by country for accordion view
        summary_rows=summary_rows,  # Keep for backward compatibility
        detailed_data=detailed_data,
        time_series_data=time_series_data,
        unit_symbols=unit_symbols,  # Pass unit symbols: {1: 'kt CO₂-eq', 5: 'kt', 6: 't'}
        region_avg_by_year=region_avg_by_year,  # For region comparison (B2)
        global_avg_by_year=global_avg_by_year,  # Global average CO₂ per capita by year
        top_risers=top_risers,  # Top 5 increases (B1)
        top_decliners=top_decliners,  # Top 5 decreases (B1)
        country_coverage=country_coverage,  # Data coverage per country (D2)
        current_country=country_name,
        current_year_min=year_min,
        current_year_max=year_max,
        latest_year_only=latest_year_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
    )


# ---------- AUTOCOMPLETE ENDPOINT ----------
@ghg_bp.route("/api/countries", methods=["GET"])
def autocomplete_countries():
    """Return countries for autocomplete"""
    query = request.args.get("q", "", type=str)
    db_conn = get_db()
    cursor = db_conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT DISTINCT country_name, country_code, region
            FROM countries
            WHERE country_name LIKE %s
            ORDER BY country_name
            LIMIT 20
            """,
            (f"%{query}%",)
        )
        countries = cursor.fetchall()
    except MySQLError:
        countries = []
    finally:
        cursor.close()

    return {"countries": countries}


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


# ---------- MAP VISUALIZATION ----------
@ghg_bp.route("/map", methods=["GET"])
def map_ghg():
    """Display map visualization for GHG data with Country Mode and Region Mode.
    All region information is derived exclusively from the countries.region column."""
    # Get available years and indicators for filters
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get available years
        cursor.execute("SELECT DISTINCT year FROM greenhouse_emissions ORDER BY year DESC")
        years = [row['year'] for row in cursor.fetchall()]
        
        # Get available indicators
        cursor.execute("SELECT ghg_indicator_id, indicator_name FROM ghg_indicator_details ORDER BY ghg_indicator_id")
        indicators = cursor.fetchall()
        
        # Get unique regions from countries table (single source of truth)
        cursor.execute("SELECT DISTINCT region FROM countries WHERE region IS NOT NULL ORDER BY region")
        regions = [row['region'] for row in cursor.fetchall()]
        
        # Get country-to-region mapping from countries table
        # This will be used to map ISO2 codes to regions for the map
        cursor.execute("""
            SELECT 
                country_code,
                region,
                country_name
            FROM countries
            WHERE country_code IS NOT NULL AND region IS NOT NULL
            ORDER BY country_code
        """)
        country_region_map = {row['country_code'].upper(): row['region'] for row in cursor.fetchall()}
        country_names_map = {row['country_code'].upper(): row['country_name'] for row in cursor.fetchall()}
        
    except MySQLError as e:
        flash(f"Database error: {e}", "danger")
        years = []
        indicators = []
        regions = []
        country_region_map = {}
        country_names_map = {}
    finally:
        cursor.close()
    
    return render_template(
        "ghg_map.html", 
        years=years, 
        indicators=indicators, 
        regions=regions,
        country_region_map=country_region_map,
        country_names_map=country_names_map
    )


@ghg_bp.route("/api/region-stats", methods=["GET"])
def get_region_ghg_stats():
    """Return aggregated GHG stats for a given region, year, and indicator.
    Only counts countries with valid data in the aggregation."""
    region = request.args.get("region", type=str)
    year = request.args.get("year", type=int)
    indicator_id = request.args.get("indicator_id", type=int, default=6)  # Default: CO2 per capita
    
    if not region:
        abort(400, description="region parameter is required")
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Build WHERE clause
        where_clauses = ["c.region = %s", "g.ghg_indicator_id = %s"]
        params = [region, indicator_id]
        
        if year:
            where_clauses.append("g.year = %s")
            params.append(year)
        
        where_sql = " AND ".join(where_clauses)
        
        # Get aggregated region data
        # CRITICAL: Only count countries that have valid (non-NULL) data
        # This ensures averages are calculated by dividing by the number of contributing countries,
        # not by the total number of countries in the region
        query = f"""
            SELECT 
                c.region,
                COUNT(DISTINCT c.country_id) as country_count,
                AVG(g.indicator_value) as avg_value,
                MIN(g.indicator_value) as min_value,
                MAX(g.indicator_value) as max_value,
                SUM(g.indicator_value) as total_value,
                GROUP_CONCAT(DISTINCT c.country_name ORDER BY c.country_name SEPARATOR ', ') as countries
            FROM countries c
            INNER JOIN greenhouse_emissions g ON c.country_id = g.country_id
            WHERE {where_sql}
            AND g.indicator_value IS NOT NULL
            GROUP BY c.region
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if not result:
            return jsonify({
                "region": region,
                "year": year,
                "indicator_id": indicator_id,
                "country_count": 0,
                "avg_value": None,
                "min_value": None,
                "max_value": None,
                "total_value": None,
                "countries": []
            })
        
        # Get indicator name
        cursor.execute(
            "SELECT indicator_name, unit_symbol FROM ghg_indicator_details WHERE ghg_indicator_id = %s",
            (indicator_id,)
        )
        indicator_info = cursor.fetchone()
        
        return jsonify({
            "region": result["region"],
            "year": year,
            "indicator_id": indicator_id,
            "indicator_name": indicator_info["indicator_name"] if indicator_info else None,
            "unit": indicator_info["unit_symbol"] if indicator_info else None,
            "country_count": result["country_count"],
            "avg_value": float(result["avg_value"]) if result["avg_value"] is not None else None,
            "min_value": float(result["min_value"]) if result["min_value"] is not None else None,
            "max_value": float(result["max_value"]) if result["max_value"] is not None else None,
            "total_value": float(result["total_value"]) if result["total_value"] is not None else None,
            "countries": result["countries"].split(", ") if result["countries"] else []
        })
        
    except MySQLError as e:
        abort(500, description=f"Database error: {e}")
    finally:
        cursor.close()
