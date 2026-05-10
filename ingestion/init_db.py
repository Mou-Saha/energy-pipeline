import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="airflow",
    user="airflow",
    password="airflow"
)

cur = conn.cursor()

cur.execute("""
    CREATE SCHEMA IF NOT EXISTS raw;

    CREATE TABLE IF NOT EXISTS raw.energy_consumption (
        id SERIAL PRIMARY KEY,
        utc_timestamp TIMESTAMP NOT NULL,
        country VARCHAR(10) NOT NULL,
        consumption_mw FLOAT,
        loaded_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(utc_timestamp, country)
    );
""")

conn.commit()
cur.close()
conn.close()

print("Table created successfully.")