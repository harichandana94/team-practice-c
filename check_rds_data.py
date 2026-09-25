import os
import psycopg
from dotenv import load_dotenv

load_dotenv(".env", override=True)

with psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
) as connection:

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, first_name, last_name, email, username, created_at
            FROM accounts
            ORDER BY id
        """)

        rows = cursor.fetchall()

        for row in rows:
            print(row)