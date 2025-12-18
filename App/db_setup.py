import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "db_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "wdi_project")
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SQL_FILE_PATH = os.path.join(BASE_DIR, 'SQL', 'database.sql') 

def setup_nuclear():
    engine_root = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}")
    
    try:
        with engine_root.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME}"))
            print(f"🗑️ The old database '{DB_NAME}' has been completely deleted.")
            
            conn.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            
    except Exception as e:
        print(f"ERROR (Root Connection): {e}")
        return

    engine_db = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")
    
    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Remove SQL single-line comments (--) and block comments (/* */) to avoid
        # splitting/mis-parsing multi-line statements that include inline comments.
        import re
        sql_clean = re.sub(r'--.*\n', '\n', sql_script)
        sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.S)

        with engine_db.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            # split into statements safely (after removing comments)
            commands = sql_clean.split(';')
            for command in commands:
                if command.strip():
                    conn.execute(text(command))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

    except FileNotFoundError:
        print(f"error:'{SQL_FILE_PATH}' could not be found.")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    setup_nuclear()
