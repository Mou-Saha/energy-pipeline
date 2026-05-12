# Energy Consumption Pipeline

A production-grade ELT pipeline ingesting hourly energy consumption data from [Open Power System Data (OPSD)](https://open-power-system-data.org/), transforming it with dbt, orchestrated by Apache Airflow, with CI/CD via GitHub Actions and infrastructure provisioned on Azure using Terraform.

Built as a portfolio project demonstrating end-to-end data engineering practices: containerization, pipeline orchestration, data transformation with testing, CI/CD automation, and infrastructure-as-code.

---

## Architecture

```
OPSD Public API
      │
      ▼
┌─────────────────┐
│  Airflow DAG    │  Orchestration layer
│                 │
│  fetch_raw_data │──► Downloads CSV (~150MB)
│       │         │    saves to /tmp
│       ▼         │
│  load_to_postgres──► raw.energy_consumption
│       │         │    (PostgreSQL)
│       ▼         │
│   dbt_run       │──► stg_energy_consumption (view)
│       │         │    mart_daily_consumption (table)
│       ▼         │
│   dbt_test      │──► Data quality checks
└─────────────────┘
```

**Data flow:**
- **Ingestion**: Python fetches hourly energy consumption for Germany, France, and Great Britain from OPSD and loads ~150k rows into PostgreSQL
- **Staging**: dbt cleans and renames columns, filters nulls, extracts date parts
- **Marts**: dbt aggregates to daily consumption metrics per country (avg, peak, min, total)
- **Tests**: dbt tests enforce not-null, accepted values, and uniqueness constraints on every run

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 2.9 |
| Transformation | dbt Core (dbt-postgres) |
| Database | PostgreSQL 15 |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Infrastructure | Terraform + Azure |
| Linting | sqlfluff |
| Language | Python 3.11 |

---

## Project Structure

```
energy-pipeline/
├── airflow/
│   └── dags/
│       └── energy_ingestion_dag.py   # Main DAG definition
├── dbt/
│   └── energy_dbt/
│       ├── models/
│       │   ├── staging/
│       │   │   ├── stg_energy_consumption.sql
│       │   │   └── schema.yml
│       │   └── marts/
│       │       ├── mart_daily_consumption.sql
│       │       └── schema.yml
│       ├── dbt_project.yml
│       └── .sqlfluff
├── ingestion/
│   ├── fetch_energy_data.py          # OPSD fetch + PostgreSQL load
│   └── init_db.py                    # Table initialisation
├── terraform/
│   ├── main.tf                       # Azure resource definitions
│   ├── variables.tf                  # Input variable declarations
│   └── outputs.tf                    # Output values
├── .github/
│   └── workflows/
│       ├── ci.yml                    # PR checks: dbt run + test + sqlfluff
│       └── cd.yml                    # Merge to main: trigger Airflow DAG
└── docker-compose.yml                # Airflow + PostgreSQL local stack
```

---

## DAG Overview

The `energy_ingestion` DAG runs daily at 06:00 UTC with the following task chain:

```
fetch_raw_data >> load_to_postgres >> dbt_run >> dbt_test
```

| Task | What it does |
|---|---|
| `fetch_raw_data` | Downloads OPSD CSV, saves to `/tmp/energy_data.csv` |
| `load_to_postgres` | Parses CSV, upserts rows into `raw.energy_consumption` |
| `dbt_run` | Runs staging view + daily mart table |
| `dbt_test` | Runs all schema tests — fails DAG if data quality breaks |

---

## dbt Models

**Staging — `stg_energy_consumption` (view)**
- Renames columns, casts timestamps, extracts `hour_of_day` and `measured_date`
- Filters out null consumption values
- Source: `raw.energy_consumption`

**Mart — `mart_daily_consumption` (table)**
- Aggregates hourly readings to daily grain per country
- Metrics: avg, peak, min, total consumption in MW, hourly reading count
- Source: `stg_energy_consumption`

**Tests:**
- `not_null` on all key columns
- `accepted_values` on `country_code` — only DE, FR, GB permitted
- Failures block the DAG from completing

---

## CI/CD

**CI pipeline** (`.github/workflows/ci.yml`) triggers on every push and PR to `main`:
1. Spins up a fresh PostgreSQL service container
2. Installs dbt + sqlfluff
3. Creates raw schema and table
4. Runs `dbt run` + `dbt test`
5. Runs `sqlfluff lint` on all SQL models

**CD pipeline** (`.github/workflows/cd.yml`) triggers on merge to `main`:
- Calls Airflow REST API to trigger the `energy_ingestion` DAG
- In production this points to the Airflow instance deployed on Azure

---

## Infrastructure (Terraform)

Provisions the following Azure resources in `northeurope`:

| Resource | Purpose |
|---|---|
| Resource Group | Logical container for all resources |
| Storage Account (ADLS Gen2) | Data lake for raw file storage |
| Storage Container `raw` | Landing zone for ingested files |
| PostgreSQL Flexible Server | Production database |
| Key Vault | Secret management |

```bash
cd terraform
terraform init
terraform plan
terraform apply   # provisions all resources
terraform destroy # tear down to avoid charges
```

---

## Running Locally

**Prerequisites:** Docker Desktop, Python 3.11, Git

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/energy-pipeline.git
cd energy-pipeline
```

**2. Create virtual environment**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install psycopg2-binary requests dbt-postgres
```

**3. Start Airflow stack**
```bash
echo "AIRFLOW_UID=50000" > .env
docker compose up airflow-init
docker compose up -d
```

**4. Initialise the database**
```bash
python ingestion/init_db.py
```

**5. Access Airflow UI**

Navigate to `http://localhost:8080` — login with `admin` / `admin`

Trigger the `energy_ingestion` DAG manually or wait for the 06:00 UTC schedule.

**6. Run dbt manually**
```bash
cd dbt/energy_dbt
dbt run
dbt test
```

---

## Data Source

[Open Power System Data](https://open-power-system-data.org/) — open-licensed hourly time series data for European energy systems. Countries covered: Germany (DE), France (FR), Great Britain (GB).