# DAG supervision des messages en erreur
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from kafka import KafkaConsumer
import json
import smtplib
from email.mime.text import MIMEText

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
    'monitoring_dlq',
    default_args=default_args,
    description='DAG supervision messages en erreur / DLQ',
    schedule_interval='@hourly',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1
)

# -----------------------------
# Configuration Kafka & Email
# -----------------------------
KAFKA_BOOTSTRAP = "kafka-cluster-kafka-bootstrap:9092"
DLQ_TOPICS = ["transactions_dlq", "kyc_responses_dlq", "crm_customers_dlq"]

EMAIL_SENDER = "alert@filerouge.com"
EMAIL_RECIPIENTS = ["ops@filerouge.com"]
SMTP_SERVER = "smtp.filerouge.com"

# -----------------------------
# Fonction de monitoring
# -----------------------------
def monitor_dlq():
    alert_messages = []

    for topic in DLQ_TOPICS:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode("utf-8"))
        )
        count = sum(1 for _ in consumer)
        if count > 0:
            alert_messages.append(f"⚠️ {count} messages en erreur dans le topic {topic}")
        consumer.close()

    if alert_messages:
        body = "\n".join(alert_messages)
        msg = MIMEText(body)
        msg['Subject'] = 'Alert DLQ File Rouge'
        msg['From'] = EMAIL_SENDER
        msg['To'] = ", ".join(EMAIL_RECIPIENTS)

        with smtplib.SMTP(SMTP_SERVER) as server:
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())

        print("📧 Alertes DLQ envoyées")
    else:
        print("✅ Aucun message en DLQ")

# -----------------------------
# Tâche Airflow
# -----------------------------
dlq_monitor_task = PythonOperator(
    task_id='monitor_dlq',
    python_callable=monitor_dlq,
    dag=dag
)
