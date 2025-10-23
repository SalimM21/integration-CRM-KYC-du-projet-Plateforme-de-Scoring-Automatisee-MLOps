# DAG orchestration ingestion CRM
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
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
    'ingestion_crm',
    default_args=default_args,
    description='DAG ingestion CRM Kafka -> Delta',
    schedule_interval='@hourly',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1
)

# -----------------------------
# Tâche 1 : Vérification des topics Kafka
# -----------------------------
check_topics = BashOperator(
    task_id='check_kafka_topics',
    bash_command='kafka-topics.sh --bootstrap-server kafka-cluster-kafka-bootstrap:9092 --list',
    dag=dag
)

# -----------------------------
# Tâche 2 : Lancer ingestion Kafka -> Delta
# -----------------------------
ingest_crm = BashOperator(
    task_id='ingest_crm',
    bash_command='spark-submit --master local[4] /opt/spark/jobs/kafka_streaming_job.py',
    dag=dag
)

# -----------------------------
# Tâche 3 : Validation JSON Schema
# -----------------------------
validate_crm = BashOperator(
    task_id='validate_crm',
    bash_command='python3 /opt/spark/jobs/test_data_validation.py',
    dag=dag
)

# -----------------------------
# Tâche 4 : Retry / DLQ handling
# -----------------------------
retry_dlq = BashOperator(
    task_id='retry_dlq',
    bash_command='python3 /opt/spark/jobs/retry_dlq_handler.py',
    dag=dag
)

# -----------------------------
# Définir l'ordre des tâches
# -----------------------------
check_topics >> ingest_crm >> validate_crm >> retry_dlq
