import sys
from App.db import db
from App.models import EnergyIndicatorDetails, SustainabilityIndicatorDetails
from sqlalchemy import text

try:
    from run import app 
except ImportError:
    print("FATAL ERROR: Could not import the main Flask app. Ensure your startup file is named 'run.py' or similar.")
    sys.exit(1)

def test_energy_data_fetch():
    with app.app_context():
        print("--- Running Energy Data Fetch Test ---")
        try:
            indicators = db.session.execute(
                db.select(EnergyIndicatorDetails)
                .order_by(EnergyIndicatorDetails.indicator_id)
            ).scalars().all()

            if indicators:
                print(f"SUCCESS: Fetched {len(indicators)} Energy Indicators.")
                print(f"Sample Indicator: {indicators[0].indicator_name}")
            else:
                print("WARNING: Connection successful, but no indicators found. Did you run the master SQL?")

        except Exception as e:
            print(f"ERROR: Failed to execute ORM query. Check DB credentials or table structure. Error: {e}")

def test_sustainability_data_fetch():
    with app.app_context():
        print("--- Running Sustainability Data Fetch Test ---")
        try:
            indicators = db.session.execute(
                db.select(SustainabilityIndicatorDetails)
                .order_by(SustainabilityIndicatorDetails.indicator_id)
            ).scalars().all()

            if indicators:
                print(f"SUCCESS: Fetched {len(indicators)} Sustainability Indicators.")
                print(f"Sample Indicator: {indicators[0].indicator_name}")
            else:
                print("WARNING: Connection successful, but no sustainability indicators found. Did you run the master SQL?")

        except Exception as e:
            print(f"ERROR: Failed to execute ORM query for sustainability. Check DB credentials or table structure. Error: {e}")

if __name__ == "__main__":
    test_energy_data_fetch()
    test_sustainability_data_fetch()
