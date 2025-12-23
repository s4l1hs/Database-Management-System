import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from App.db import get_db
from main import app


def test_energy_data_fetch():
    with app.app_context():
        print("--- Running Energy Data Fetch Test ---")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM energy_indicator_details")
            cnt = cur.fetchone().get('cnt', 0)
            if cnt:
                cur.execute("SELECT indicator_name FROM energy_indicator_details ORDER BY energy_indicator_id LIMIT 1")
                sample = cur.fetchone()
                print(f"SUCCESS: Fetched {cnt} Energy Indicators.")
                if sample:
                    print(f"Sample Indicator: {sample.get('indicator_name')}")
            else:
                print("WARNING: Connection successful, but no indicators found. Did you run the master SQL?")
        except Exception as e:
            print(f"ERROR: Failed to execute query. Check DB credentials or table structure. Error: {e}")
        finally:
            cur.close()


def test_sustainability_data_fetch():
    with app.app_context():
        print("--- Running Sustainability Data Fetch Test ---")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM sustainability_indicator_details")
            cnt = cur.fetchone().get('cnt', 0)
            if cnt:
                cur.execute("SELECT indicator_name FROM sustainability_indicator_details ORDER BY sus_indicator_id LIMIT 1")
                sample = cur.fetchone()
                print(f"SUCCESS: Fetched {cnt} Sustainability Indicators.")
                if sample:
                    print(f"Sample Indicator: {sample.get('indicator_name')}")
            else:
                print("WARNING: Connection successful, but no sustainability indicators found. Did you run the master SQL?")
        except Exception as e:
            print(f"ERROR: Failed to execute query for sustainability. Check DB credentials or table structure. Error: {e}")
        finally:
            cur.close()

def test_health_data_fetch():
    with app.app_context():
        print("--- Running Health Data Fetch Test ---")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM health_indicator_details")
            cnt = cur.fetchone().get('cnt', 0)
            if cnt:
                cur.execute("SELECT indicator_name FROM health_indicator_details ORDER BY health_indicator_id LIMIT 1")
                sample = cur.fetchone()
                print(f"SUCCESS: Fetched {cnt} Health Indicators.")
                if sample:
                    print(f"Sample Indicator: {sample.get('indicator_name')}")
            else:
                print("WARNING: Connection successful, but no health indicators found. Did you run the master SQL?")
        except Exception as e:
            print(f"ERROR: Failed to execute query for health. Check DB credentials or table structure. Error: {e}")
        finally:
            cur.close()

def test_freshwater_data_fetch():
    with app.app_context():
        print("--- Running Freshwater Data Fetch Test ---")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM freshwater_indicator_details")
            cnt = cur.fetchone().get('cnt', 0)
            if cnt:
                cur.execute("SELECT indicator_name FROM freshwater_indicator_details ORDER BY freshwater_indicator_id LIMIT 1")
                sample = cur.fetchone()
                print(f"SUCCESS: Fetched {cnt} Freshwater Indicators.")
                if sample:
                    print(f"Sample Indicator: {sample.get('indicator_name')}")
            else:
                print("WARNING: Connection successful, but no freshwater indicators found. Did you run the master SQL?")
        except Exception as e:
            print(f"ERROR: Failed to execute query for freshwater. Check DB credentials or table structure. Error: {e}")
        finally:
            cur.close()

def test_ghg_data_fetch():
    with app.app_context():
        print("--- Running GHG Data Fetch Test ---")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM ghg_indicator_details")
            cnt = cur.fetchone().get('cnt', 0)
            if cnt:
                cur.execute("SELECT indicator_name FROM ghg_indicator_details ORDER BY ghg_indicator_id LIMIT 1")
                sample = cur.fetchone()
                print(f"SUCCESS: Fetched {cnt} GHG Indicators.")
                if sample:
                    print(f"Sample Indicator: {sample.get('indicator_name')}")
            else:
                print("WARNING: Connection successful, but no GHG indicators found. Did you run the master SQL?")
        except Exception as e:
            print(f"ERROR: Failed to execute query for GHG. Check DB credentials or table structure. Error: {e}")
        finally:
            cur.close()

def test_countries_data_fetch():
    with app.app_context():
        print("--- Running Countries Data Fetch Test ---")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS cnt FROM countries")
            cnt = cur.fetchone().get('cnt', 0)
            if cnt:
                cur.execute("SELECT country_name FROM countries ORDER BY country_id LIMIT 1")
                sample = cur.fetchone()
                print(f"SUCCESS: Fetched {cnt} Countries.")
                if sample:
                    print(f"Sample Country: {sample.get('country_name')}")
            else:
                print("WARNING: Connection successful, but no countries found. Did you run the master SQL?")
        except Exception as e:
            print(f"ERROR: Failed to execute query for countries. Check DB credentials or table structure. Error: {e}")
        finally:
            cur.close()


if __name__ == "__main__":
    test_energy_data_fetch()
    test_sustainability_data_fetch()
    test_health_data_fetch()
    test_freshwater_data_fetch()
    test_ghg_data_fetch()
    test_countries_data_fetch()
