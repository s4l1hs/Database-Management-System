from flask import Blueprint, render_template
from App.db import get_db

ghg_bp = Blueprint("ghg", __name__)

@ghg_bp.route("/", methods=["GET"])
def list_ghg():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT g.row_id,
               c.country_name,
               c.region,
               c.country_code,
               i.indicator_name,
               i.indicator_code,
               i.source_note,
               g.year,
               g.indicator_value
        FROM ghg_data g
        JOIN countries c ON c.country_id = g.country_id
        JOIN ghg_indicator_details i ON i.indicator_id = g.indicator_id
        ORDER BY c.country_name, i.indicator_name, g.year
    """)
    rows = cur.fetchall()
    return render_template("ghg_list.html", rows=rows)
