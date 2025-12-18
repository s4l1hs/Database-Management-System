import os
import re
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "db_pass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "wdi_project")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SQL_FILE_PATH = os.path.join(BASE_DIR, 'SQL', 'database.sql')


def _exec_statements(cursor, sql_text: str):
    # remove single-line and block comments, then split on semicolon
    sql_clean = re.sub(r'--.*\n', '\n', sql_text)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.S)
    commands = [c.strip() for c in sql_clean.split(';') if c.strip()]
    for cmd in commands:
        cursor.execute(cmd)


def setup_nuclear():
    # connect as root (no database) to drop/create the database
    try:
        conn_root = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT)
        conn_root.autocommit = True
        cur = conn_root.cursor()
        try:
            cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`")
            print(f"🗑️ The old database '{DB_NAME}' has been completely deleted.")
            cur.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        finally:
            cur.close()
    except Exception as e:
        print(f"ERROR (Root Connection): {e}")
        return
    finally:
        try:
            conn_root.close()
        except Exception:
            pass

    # connect to the newly created database and run SQL script
    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
    except FileNotFoundError:
        print(f"error:'{SQL_FILE_PATH}' could not be found.")
        return

    try:
        conn_db = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT, database=DB_NAME)
        conn_db.autocommit = True
        cur = conn_db.cursor()
        try:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            _exec_statements(cur, sql_script)
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        finally:
            cur.close()
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
    finally:
        try:
            conn_db.close()
        except Exception:
            pass


if __name__ == "__main__":
    setup_nuclear()
