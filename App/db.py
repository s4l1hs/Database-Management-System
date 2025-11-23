# App/db.py
import mysql.connector
from flask import g
from flask_sqlalchemy import SQLAlchemy
import os

# 1. ORM Nesnesi (Yeni Puan Kazandıran Yapı)
# models.py ve app.py bunu kullanacak.
db = SQLAlchemy()

# Environment variables will come from .env file
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "db_pass"),
    "database": os.getenv("DB_NAME", "world_dev_indicators"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

def get_db():
    """
    It creates a single MySQL connection for Flask's request context and caches it via g.
    """
    if "db" not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db

def close_db(e=None):
    """
    When the request is completed, it closes the MySQL connection.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()
