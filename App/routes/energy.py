from flask import Blueprint, render_template
from db import get_db 


energy_bp = Blueprint("energy", __name__) 

@energy_bp.route("/", methods=["GET"])
def list_energy_data():
    db = get_db()
    cur = db.cursor(dictionary=True) 
    cur.execute("""
        SELECT 
            e.row_id,
            c.country_name,
            c.region,
            c.country_code,
            i.indicator_name,
            i.indicator_description, 
            i.unit_of_measure,
            e.year,
            e.value
        FROM energy_data e
        JOIN countries c ON c.country_id = e.country_id
        JOIN energy_indicator_details i ON i.indicator_id = e.indicator_id
        ORDER BY c.country_name, i.indicator_name, e.year
    """)

    rows = cur.fetchall()
    return render_template('energy_list.html', rows=rows)
