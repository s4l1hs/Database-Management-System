import sys
import os
from dotenv import load_dotenv
 
# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
 
# Load .env file from project root
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)
 
from App.routes import create_app  # type: ignore
from App.db import get_db
 
 
def seed_students() -> None:
    """
    Seed admin and editor users into the students table.
 
    - Admins: team_no = 1
    - Editor: student_number = 5454, team_no = 2
    """
    db = get_db()
    cur = db.cursor()
 
    # If student_number is UNIQUE, this will upsert; if not, it will simply insert new rows.
    sql = """
        INSERT INTO students (student_number, full_name, team_no)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
          full_name = VALUES(full_name),
          team_no   = VALUES(team_no)
    """
 
    rows = [
        # Admin users (team_no = 1)
        ('820230313', 'Salih Sefer', 1),
        ('820230334', 'Atahan Evintan', 1),
        ('820230326', 'Fatih Serdar Çakmak', 1),
        ('820230314', 'Muhammet Tuncer', 1),
        ('150210085', 'Gülbahar Karabaş', 1),
        # Editor user (team_no = 2)
        ('5454', 'Editor User', 2),
    ]
 
    for sn, name, team in rows:
        cur.execute(sql, (sn, name, team))
 
    db.commit()
    cur.close()
    print("Successfully seeded students!")
 
 
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_students()
 
 
 
 
