import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "sentiment_user"),
    "password": os.environ.get("DB_PASSWORD", "sentiment_pass"),
    "database": os.environ.get("DB_NAME", "sentiment_db"),
}