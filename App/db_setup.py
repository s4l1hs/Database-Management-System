import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DB_USER = "root"
DB_PASS = "db_pass" 
DB_HOST = "localhost"
DB_NAME = "wdi_project"
SQL_FILE_PATH = os.path.join('../SQL','database.sql') 

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
            
        with engine_db.connect() as conn:
            commands = sql_script.split(';')
            for command in commands:
                if command.strip():
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                    conn.execute(text(command))
            
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            conn.commit()

    except FileNotFoundError:
        print(f"error:'{SQL_FILE_PATH}' could not be found.")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    setup_nuclear()