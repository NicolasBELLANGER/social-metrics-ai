import mysql.connector
from config import DB_CONFIG


def get_connection():
    """Ouvre une connexion à la base MySQL. A fermer avec conn.close()."""
    return mysql.connector.connect(**DB_CONFIG)