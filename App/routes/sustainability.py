from flask import Blueprint, render_template
from db import get_db

sustainability_bp = Blueprint("sustainability", __name__)

@sustainability_bp.route("/", methods=["GET"])
def list_sustainability():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT s.data_id,
               c.country_name,
               c.region,
               c.country_code,
               i.indicator_name,
               i.indicator_code,
               i.source_note,
               s.year,
               s.value
        FROM sustainability_data s
        JOIN countries c ON c.country_id = s.country_id
        JOIN sustainability_indicator_details i ON i.indicator_id = s.indicator_id
        ORDER BY c.country_name, i.indicator_name, s.year
    """)

    rows = cur.fetchall()
    return render_template("sustainability_list.html", rows=rows)

