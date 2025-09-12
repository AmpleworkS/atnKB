import json
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

with open("data (4).json", "r", encoding="utf-8") as f:
    records = json.load(f)  # This should now be a list

insert_query = """
INSERT INTO atn_table (
    "Customer ID", "Customer Name") VALUES (
    %(Customer ID)s, %(Customer Name)s
    )
"""

for rec in records:
    data = {
        "Customer ID": rec.get("Customer ID"),
        "Customer Name": rec.get("Customer Name")
    }
    cur.execute(insert_query, data)

conn.commit()
cur.close()
conn.close()

print("✅ All JSON records inserted into PostgreSQL successfully!")