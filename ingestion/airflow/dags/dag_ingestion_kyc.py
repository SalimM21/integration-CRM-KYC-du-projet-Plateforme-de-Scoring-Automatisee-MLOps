# DAG batch KYC
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import subprocess

# -----------------------------
# DAG Configuration
# -----------------------------
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ingestion_kyc',
    default_args=default_args,
    description='DAG batch ingestion KYC API -> Delta',
    schedule_interval='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1
)

# -----------------------------
# Tâche 1 : Extraire KYC via batch
# -----------------------------
def extract_kyc():
    subprocess.run(["python3", "/opt/spark/jobs/enrich_kyc_batch.ipynb"], check=True)

extract_task = PythonOperator(
    task_id='extract_kyc_batch',
    python_callable=extract_kyc,
    dag=dag
)

# -----------------------------
# Tâche 2 : Validation JSON Schema
# -----------------------------
def validate_kyc():
    subprocess.run(["python3", "/opt/spark/jobs/test_data_validation.py"], check=True)

validate_task = PythonOperator(
    task_id='validate_kyc',
    python_callable=validate_kyc,
    dag=dag
)

# -----------------------------
# Tâche 3 : Retry / DLQ handling
# -----------------------------
def handle_dlq():
    subprocess.run(["python3", "/opt/spark/jobs/retry_dlq_handler.py"], check=True)

retry_task = PythonOperator(
    task_id='retry_dlq_kyc',
    python_callable=handle_dlq,
    dag=dag
)

# -----------------------------
# Définir l'ordre des tâches
# -----------------------------
extract_task >> validate_task >> retry_task

