# App/db.py

import os
import mysql.connector
from flask import g

# Database configuration loaded from environment variables
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "db_pass"),
    "database": os.getenv("DB_NAME", "wdi_project"),
    "port": int(os.getenv("DB_PORT", "3306")),
}


def get_db():
    """
    Returns a single MySQL connection for the current Flask request context.
    The connection is cached in flask.g to avoid reconnecting multiple times.
    """
    if "db" not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db


def close_db(e=None):
    """
    Closes the MySQL connection at the end of the request, if it exists.
    This function is meant to be registered with app.teardown_appcontext.
    """
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
