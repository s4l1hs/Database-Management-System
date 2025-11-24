from flask import Blueprint, render_template
from App.db import get_db


freshwater_bp = Blueprint("freshwater", __name__)
@freshwater_bp.route("/", methods=["GET"])
def list_freshwater():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT f.data_id,
               c.country_name,
               c.region,
               c.country_code,
               i.indicator_name,
               i.indicator_description,
               i.unit_of_measure,
               f.year,
               f.value
        FROM freshwater_data f
        JOIN countries c ON c.country_id = f.country_id
        JOIN freshwater_indicator_details i ON i.indicator_id = f.indicator_id
        ORDER BY c.country_name, i.indicator_name, f.year
    """)

    rows = cur.fetchall()
    
   
    return render_template("freshwater_list.html", rows=rows)

  
