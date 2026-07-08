import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "sentiment-api-user"),
    "password": os.environ.get("DB_PASSWORD", "sentiment-api-pass"),
    "database": os.environ.get("DB_NAME", "sentiment-api-db"),
}