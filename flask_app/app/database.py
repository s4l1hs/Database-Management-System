import mysql.connector


def get_db():
    """Establish a connection to the MySQL database and wrap it."""
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="xxxx",
        database="wdi",
    )
    return ConnectionWrapper(conn)


class ConnectionWrapper:
    """A simple wrapper for MySQL connection providing custom query methods."""

    def __init__(self, conn):
        self.conn = conn

    def get_greenhouse_data(self):
        """Retrieve greenhouse gas emission data for a subset of records."""
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT country, year, total_emissions
            FROM greenhouse_gas
            LIMIT 50
            """
        )
        return cursor.fetchall()
