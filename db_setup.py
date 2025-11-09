import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DB_USER = "root"
DB_PASS = "sifren"
DB_HOST = "localhost"
DB_NAME = "wdi_project"

SQL_FILE_PATH = os.path.join('SQL', 'master.sql')

def setup_database():
    try:
        engine_url_root = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}"
        root_engine = create_engine(engine_url_root)

        with root_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"Database '{DB_NAME}' checked/created.")

        engine_url_db = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
        db_engine = create_engine(engine_url_db)

        try:
            with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
                sql_script = f.read()
        except FileNotFoundError:
            print(f"HATA: '{SQL_FILE_PATH}' dosyası bulunamadı.")
            return

        with db_engine.connect() as conn:
            commands = sql_script.split(';')
            print(f"Executing commands from '{SQL_FILE_PATH}'...")
            
            for command in commands:
                if command.strip():
                    conn.execute(text(command))
            
            conn.commit()
            print("Success! All tables created and sample data inserted.")

    except OperationalError as e:
        if "Access denied" in str(e):
            print(f"HATA: MySQL bağlantısı başarısız. Kullanıcı adı veya şifre hatalı.")
        else:
            print(f"Veritabanı hatası: {e}")
    except Exception as e:
        print(f"Beklenmedik hata: {e}")

if __name__ == "__main__":
    setup_database()