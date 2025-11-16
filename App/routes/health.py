# App/routes/health.py
from flask import Blueprint, render_template
from db import get_db

#blueprints
health_bp = Blueprint("health", __name__) # Blueprint name: health

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
               i.indicator_description,
               i.unit_symbol        
               h.year,
               h.indicator_value,              
        FROM health_system h
        JOIN countries c ON c.country_id = h.country_id
        JOIN health_indicator_details i ON i.indicator_id = h.indicator_id
        ORDER BY c.country_name, i.indicator_name, h.year
    """)

    rows = cur.fetchall()
    return render_template("health_list.html", rows=rows)
