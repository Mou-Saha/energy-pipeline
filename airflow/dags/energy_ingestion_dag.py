from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/opt/airflow/ingestion")
from fetch_energy_data import fetch_data, parse_and_load

TEMP_FILE = "/tmp/energy_data.csv"
DBT_PROJECT_DIR = "/opt/airflow/dbt/energy_dbt"

default_args = {
    "owner": "sounak",
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
    description="Ingest and transform hourly energy consumption data",
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

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --profiles-dir {DBT_PROJECT_DIR}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test --profiles-dir {DBT_PROJECT_DIR}",
    )

    fetch_task >> load_task >> dbt_run >> dbt_test