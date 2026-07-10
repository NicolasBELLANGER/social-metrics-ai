import csv
from pathlib import Path

from db.connection import get_connection

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "tweet-dataset.csv"


def seed_if_empty():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tweets")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"Base déjà peuplée ({count} tweets), seed ignoré.")
        cursor.close()
        conn.close()
        return

    inserted = _import_csv(cursor)
    conn.commit()
    print(f"{inserted} tweets importés.")
    cursor.close()
    conn.close()


def sync_missing_tweets():
    """Ajoute les tweets du CSV absents de la base (sans dupliquer)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM tweets")
    existing = {row[0] for row in cursor.fetchall()}

    inserted = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["text"] in existing:
                continue
            cursor.execute(
                "INSERT INTO tweets (text, positive, negative) VALUES (%s, %s, %s)",
                (row["text"], int(row["positive"]), int(row["negative"])),
            )
            inserted += 1

    conn.commit()
    if inserted:
        print(f"{inserted} nouveau(x) tweet(s) ajouté(s) depuis le CSV.")
    cursor.close()
    conn.close()


def _import_csv(cursor):
    inserted = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(
                "INSERT INTO tweets (text, positive, negative) VALUES (%s, %s, %s)",
                (row["text"], int(row["positive"]), int(row["negative"])),
            )
            inserted += 1
    return inserted


if __name__ == "__main__":
    seed_if_empty()
