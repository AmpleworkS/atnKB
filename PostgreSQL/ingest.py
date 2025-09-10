import json
import psycopg2
import os

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

with open("data (2).json", "r", encoding="utf-8") as f:
    records = json.load(f)  # This should now be a list

insert_query = """
INSERT INTO atn_table (
    "Customer ID", "Customer Name", "Email", "Phone Number", "country", "Sales_Rep Name", "Qualifying Lead", "Lead qualification Reason", "Ad Lead Qualification Reason",  "Ad Lead", 
    "Package of Customer Interest","Package Purchased","Postal Code", "Pain points Objections Outcomes", "Tags from GHL","Investment Level", "Investable Assets","Engagement Level", "Risk Profile", "Persona Type"
) VALUES (
    %(Customer ID)s, %(Customer Name)s, %(Email)s, %(Phone Number)s, %(country)s, %(Sales_Rep Name)s, %(Qualifying Lead)s, %(Lead qualification Reason)s, %(Ad Lead Qualification Reason)s,
    %(Ad Lead)s,
    %(Package of Customer Interest)s,%(Package Purchased)s, %(Postal Code)s, %(Pain points Objections Outcomes)s, %(Tags from GHL)s, %(Investment Level)s, %(Investable Assets)s, %(Engagement Level)s, %(Risk Profile)s, %(Persona Type)s
)
"""

for rec in records:
    data = {
        "Customer ID": rec.get("Customer ID"),
        "Customer Name": rec.get("Customer Name"),
        "Email": rec.get("Email"),
        "Phone Number": rec.get("Phone Number"),
        "country": rec.get("country"),
        "Sales_Rep Name": rec.get("Sales_Rep Name"),
        "Qualifying Lead": rec.get("Qualifying Lead") == "True",
        "Lead qualification Reason": rec.get("Lead qualification Reason"),
        "Ad Lead Qualification Reason": rec.get("Ad Lead Qualification Reason"),
        "Package Purchased": rec.get("Package Purchased"),
        "Postal Code": rec.get("Postal Code"),
        "Ad Lead": rec.get("Ad Lead") == "True",
        "Package of Customer Interest": rec.get("Package of Customer Interest"),
        "Pain points Objections Outcomes": rec.get("Pain points Objections Outcomes"),
        "Tags from GHL": rec.get("Tags from GHL"),
        "Investment Level": rec.get("Investment Level"),
        "Investable Assets": rec.get("Investable Assets"),
        "Engagement Level": rec.get("Engagement Level"),
        "Risk Profile": rec.get("Risk Profile"),
        "Persona Type": rec.get("Persona Type"),

    }
    cur.execute(insert_query, data)

conn.commit()
cur.close()
conn.close()

print("✅ All JSON records inserted into PostgreSQL successfully!")