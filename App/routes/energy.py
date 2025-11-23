from flask import Blueprint, render_template
from db import get_db 

energy_bp = Blueprint("energy", __name__) 

# =========================================================
# 1. READ: Basic List (Route: /energy)
# =========================================================
@energy_bp.route("/energy", methods=["GET"])
def list_energy_data():
    """Retrieves all comprehensive energy data for the main list view."""
    db = get_db()
    cur = db.cursor(dictionary=True) 
    
    cur.execute("""
        SELECT 
            e.data_id,                 
            c.country_name,
            c.region,
            c.country_code,
            i.indicator_name,
            i.measurement_unit,       
            e.year,
            e.indicator_value        
        FROM energy_data e
        JOIN countries c ON c.country_id = e.country_id
        JOIN energy_indicator_details i ON i.energy_indicator_id = e.energy_indicator_id
        ORDER BY c.country_name, i.indicator_name, e.year
        LIMIT 200
    """)

    rows = cur.fetchall()
    return render_template('energy_list.html', rows=rows)


# =========================================================
# 2. READ: Parametric Filtering (Route: /energy/<int:country_id>)
# =========================================================
@energy_bp.route("/energy/<int:country_id>", methods=["GET"])
def list_energy_by_country(country_id):
    """Retrieves and displays all Energy data specific to a given country ID."""
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            e.data_id,
            c.country_name,
            c.region,
            i.indicator_name,
            i.measurement_unit,
            e.year,
            e.indicator_value
        FROM energy_data e
        JOIN countries c ON c.country_id = e.country_id
        JOIN energy_indicator_details i ON i.energy_indicator_id = e.energy_indicator_id
        WHERE c.country_id = %s
        ORDER BY i.indicator_name, e.year
    """, (country_id,)) 

    rows = cur.fetchall()
    
    country_name = rows[0]['country_name'] if rows else "Veri Bulunamayan Ülke"

    return render_template(
        "energy_country.html", 
        rows=rows,
        country_name=country_name
    )


# =========================================================
# 3. READ: Analytic Analysis (Route: /energy/ranking)
# =========================================================
@energy_bp.route("/energy/ranking", methods=["GET"])
def energy_ranking():
    """Analyzes and ranks countries based on their average renewable energy consumption."""
    db = get_db()
    cur = db.cursor(dictionary=True) 

    cur.execute("""
        SELECT
            c.country_name,
            c.region,
            AVG(e.indicator_value) AS avg_renewable_consumption 
        FROM energy_data e
        JOIN countries c ON c.country_id = e.country_id
        JOIN energy_indicator_details i ON i.energy_indicator_id = e.energy_indicator_id
        WHERE 
            i.indicator_code = 'EG.FEC.RNEW.ZS' 
        GROUP BY 
            c.country_name, c.region
        HAVING 
            AVG(e.indicator_value) IS NOT NULL 
        ORDER BY 
            avg_renewable_consumption DESC
        LIMIT 20;
    """)

    ranking_data = cur.fetchall()
        
    return render_template('energy_ranking.html', 
                           analysis_data=ranking_data,
                           title="Top 20 Renewable Energy Consumers")
