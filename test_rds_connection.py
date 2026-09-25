import os
import psycopg
from dotenv import load_dotenv

load_dotenv(".env", override=True)

try:
    connection = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=10
    )

    print("SUCCESS: Connected to Amazon RDS PostgreSQL")

    connection.close()

except Exception as error:
    print("FAILED:")
    print(error)