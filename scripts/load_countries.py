import os
import csv
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "db_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "wdi_project")

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data', 'countries.csv')

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

def load():
    with engine.begin() as conn:
        # disable FK checks while truncating/inserting
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
        conn.execute(text("TRUNCATE TABLE countries;"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

        with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            for r in reader:
                # normalize fields
                cid = int(r.get('country_id') or 0)
                name = r.get('country_name') or ''
                code = r.get('country_code') or ''
                region = r.get('region') or ''
                rows.append({'country_id': cid, 'country_name': name.strip(), 'country_code': code.strip(), 'region': region.strip()})

            insert_sql = text(
                "INSERT INTO countries (country_id, country_name, country_code, region) VALUES (:country_id, :country_name, :country_code, :region)"
            )

            for row in rows:
                conn.execute(insert_sql, row)

    print(f"Loaded {len(rows)} countries from {CSV_PATH}")

if __name__ == '__main__':
    load()
