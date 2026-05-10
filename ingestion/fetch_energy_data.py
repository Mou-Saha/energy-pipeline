import requests
import psycopg2
import csv
import io
from datetime import datetime


OPSD_URL = (
    #smaller file
   "https://data.open-power-system-data.org/time_series/2020-10-06/time_series_60min_singleindex.csv"
    #bigger file
    #"https://data.open-power-system-data.org/time_series/latest/time_series_60min_singleindex.csv"
)

COUNTRIES = ["DE", "FR", "GB"]

COUNTRY_COLUMNS = {
    "DE": "DE_load_actual_entsoe_transparency",
    "FR": "FR_load_actual_entsoe_transparency",
    "GB": "GB_GBN_load_actual_entsoe_transparency",
}


def fetch_data():
    print("Fetching OPSD data...")
    response = requests.get(OPSD_URL, timeout=60)
    response.raise_for_status()
    print("Download complete.")
    return response.text


def parse_and_load(csv_text: str):
    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        dbname="airflow",
        user="airflow",
        password="airflow"
    )
    cur = conn.cursor()

    reader = csv.DictReader(io.StringIO(csv_text))
    rows_inserted = 0
    rows_skipped = 0

    for row in reader:
        utc_timestamp = row.get("utc_timestamp", "").strip()
        if not utc_timestamp:
            continue

        try:
            ts = datetime.fromisoformat(utc_timestamp.replace("Z", "+00:00"))
        except ValueError:
            continue

        for country, col in COUNTRY_COLUMNS.items():
            raw_value = row.get(col, "").strip()
            consumption = float(raw_value) if raw_value else None

            try:
                cur.execute("""
                    INSERT INTO raw.energy_consumption
                        (utc_timestamp, country, consumption_mw)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (utc_timestamp, country) DO NOTHING
                """, (ts, country, consumption))
                rows_inserted += 1
            except Exception as e:
                rows_skipped += 1
                print(f"Skipped row: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done. Inserted: {rows_inserted}, Skipped: {rows_skipped}")


if __name__ == "__main__":
    csv_text = fetch_data()
    parse_and_load(csv_text)