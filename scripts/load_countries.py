import os
import csv
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "db_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "wdi_project")

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Data', 'countries.csv')


def load():
    rows = []
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for r in reader:
            cid = int(r.get('country_id') or 0)
            name = (r.get('country_name') or '').strip()
            code = (r.get('country_code') or '').strip()
            region = (r.get('region') or '').strip()
            rows.append((cid, name, code, region))

    if not rows:
        print(f"No countries found in {CSV_PATH}")
        return

    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, port=DB_PORT)
    try:
        cur = conn.cursor()
        try:
            cur.execute("SET FOREIGN_KEY_CHECKS=0;")
            cur.execute("TRUNCATE TABLE countries;")
            insert_sql = "INSERT INTO countries (country_id, country_name, country_code, region) VALUES (%s, %s, %s, %s)"
            cur.executemany(insert_sql, rows)
            cur.execute("SET FOREIGN_KEY_CHECKS=1;")
        finally:
            cur.close()
        conn.commit()
    finally:
        conn.close()

    print(f"Loaded {len(rows)} countries from {CSV_PATH}")


if __name__ == '__main__':
    load()
