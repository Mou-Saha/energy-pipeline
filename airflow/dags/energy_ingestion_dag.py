from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/opt/airflow/ingestion")

from fetch_energy_data import fetch_data, parse_and_load

TEMP_FILE = "/tmp/energy_data.csv"

default_args = {
    "owner": "Mou",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def fetch_and_save():
    csv_text = fetch_data()
    with open(TEMP_FILE, "w") as f:
        f.write(csv_text)
    print(f"Saved to {TEMP_FILE}")

def load_from_file():
    with open(TEMP_FILE, "r") as f:
        csv_text = f.read()
    parse_and_load(csv_text)

with DAG(
    dag_id="energy_ingestion",
    default_args=default_args,
    description="Ingest hourly energy consumption data from OPSD",
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["energy", "ingestion"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_raw_data",
        python_callable=fetch_and_save,
    )

    load_task = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_from_file,
    )

    fetch_task >> load_task