"""
DAG pour l'ingestion des données CRM et KYC
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.apache.kafka.operators.kafka import KafkaProducerOperator
from datetime import datetime, timedelta
from typing import Dict, Any
import json
import logging

# Configuration par défaut
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 9),
    'email': ['monitoring@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def validate_data(**context) -> Dict[str, Any]:
    """
    Valide les données avant ingestion
    """
    # TODO: Implémenter la validation des données
    logging.info("Validation des données en cours...")
    return {"validation_status": "success"}

def prepare_kafka_message(**context) -> str:
    """
    Prépare le message pour Kafka
    """
    ti = context['task_instance']
    validation_result = ti.xcom_pull(task_ids='validate_data')
    
    message = {
        'timestamp': datetime.now().isoformat(),
        'source': 'crm_kyc_ingestion',
        'validation_status': validation_result['validation_status'],
        'data': {
            # TODO: Ajouter les données réelles
            'customer_id': '12345',
            'operation_type': 'update'
        }
    }
    return json.dumps(message)

# Création du DAG
with DAG(
    'crm_kyc_ingestion',
    default_args=default_args,
    description='Ingestion des données CRM et KYC',
    schedule_interval=timedelta(hours=1),
    catchup=False
) as dag:

    # Tâche de validation des données
    validate_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True
    )

    # Tâche Spark pour le traitement des données
    spark_process = SparkSubmitOperator(
        task_id='spark_process',
        application='/opt/airflow/dags/scripts/process_crm_kyc.py',
        conf={
            'spark.master': 'local[*]',
            'spark.driver.memory': '2g',
            'spark.executor.memory': '2g'
        },
        verbose=True
    )

    # Tâche pour envoyer les données à Kafka
    kafka_send = KafkaProducerOperator(
        task_id='send_to_kafka',
        kafka_config_id='kafka_default',
        topic='crm_kyc_updates',
        python_callable=prepare_kafka_message,
        provide_context=True
    )

    # Définir l'ordre des tâches
    validate_task >> spark_process >> kafka_send