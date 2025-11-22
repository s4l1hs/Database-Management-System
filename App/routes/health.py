# App/routes/health.py
from flask import Blueprint, render_template
from db import get_db

#blueprints
health_bp = Blueprint("health", __name__) # Blueprint name: health


#list health records with some details of all countries
@health_bp.route("/", methods=["GET"])
def list_health():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT h.row_id,
               c.country_name,
               c.region,
               c.country_code, 
               i.indicator_name,
               i.unit_symbol,   
               h.year,
               h.indicator_value              
        FROM health_system h
        JOIN countries c ON c.country_id = h.country_id
        JOIN health_indicator_details i ON i.indicator_id = h.indicator_id
        ORDER BY c.country_name, i.indicator_name, h.year
    """)

    rows = cur.fetchall()
    return render_template("health_list.html", rows=rows)

#list health records for specific country
@health_bp.route("/country/<int:country_id>", methods=["GET"])
def list_health_by_country(country_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            h.country_id,
            c.country_name,
            c.region,
            c.country_code,
            i.indicator_name,
            i.indicator_description,
            i.unit_symbol,
            h.year,
            h.indicator_value,
            h.source_notes
        FROM health_system h
        JOIN countries c 
            ON c.country_id = h.country_id
        JOIN health_indicator_details i 
            ON i.indicator_id = h.indicator_id
        WHERE h.country_id = %s
        ORDER BY h.year, i.indicator_name
    """, (country_id,))

    rows = cur.fetchall()

    country_name = rows[0]["country_name"] if rows else "Unknown Country"

    return render_template(
        "health_country.html",
        rows=rows,
        country_name=country_name
    )
#other methods will be added soon