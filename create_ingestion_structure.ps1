# ===============================================
# Script PowerShell : création d'arborescence ingestion/
# Auteur : Salim Majide
# ===============================================

$root = "ingestion"

function New-File {
    param(
        [string]$path,
        [string]$content = ""
    )
    $dir = Split-Path $path
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    Set-Content -Path $path -Value $content
    Write-Host "✅ Créé : $path"
}

# ===============================================
# Kafka
# ===============================================
New-File "$root/kafka/connect/connectors/debezium-crm-source.json" "# Connecteur Debezium pour CRM (Postgres/MySQL)"
New-File "$root/kafka/connect/connectors/jdbc-sink-dwh.json" "# Sink JDBC vers Postgres ou Data Warehouse"
New-File "$root/kafka/connect/connectors/s3-sink-minio.json" "# Sink vers MinIO/S3"
New-File "$root/kafka/connect/connectors/kyc-api-source.json" "# (Optionnel) Connecteur REST API pour KYC"

New-File "$root/kafka/connect/config/connect-distributed.properties" "# Configuration principale du worker Connect"
New-File "$root/kafka/connect/config/secrets.env" "# Variables secrètes (vault ou k8s secrets)"
New-File "$root/kafka/connect/config/log4j.properties" "# Configuration des logs Connect"

New-File "$root/kafka/topics/crm_customers.avsc" "# Schéma Avro pour les données CRM"
New-File "$root/kafka/topics/transactions.avsc" "# Schéma Avro pour les transactions"
New-File "$root/kafka/topics/kyc_response_schema.json" "# Schéma JSON pour la validation KYC"
New-File "$root/kafka/topics/topic_config.yaml" "# Config topics (partitions, retention, DLQ)"

New-File "$root/kafka/scripts/create_topics.sh" "# Script d’automatisation création topics"
New-File "$root/kafka/scripts/deploy_connectors.sh" "# Script curl vers API Kafka Connect"
New-File "$root/kafka/scripts/test_ingestion.py" "# Test d’ingestion (latence, volumétrie)"

New-File "$root/kafka/manifests/kafka-cluster.yaml" "# CRD Strimzi Kafka (avec persistence + secrets)"
New-File "$root/kafka/manifests/kafka-connect.yaml" "# Déploiement Connect (Strimzi)"
New-File "$root/kafka/manifests/secret-kafka.yaml" "# Secret Kubernetes / Vault reference"
New-File "$root/kafka/manifests/k8s-pvc.yaml" "# Volumes persistants"
New-File "$root/kafka/manifests/vault-policy.hcl" "# Policy HashiCorp Vault pour accès secrets"

# ===============================================
# Spark
# ===============================================
New-File "$root/spark/notebooks/streaming_kafka_to_delta.ipynb" "# Notebook PySpark (Kafka → Delta)"
New-File "$root/spark/notebooks/validate_json_schema.ipynb" "# Validation JSON schema des messages"
New-File "$root/spark/notebooks/enrich_kyc_batch.ipynb" "# Intégration API KYC et stockage"
New-File "$root/spark/notebooks/monitoring_drift.ipynb" "# (Optionnel) Monitoring qualité data"

New-File "$root/spark/jobs/kafka_streaming_job.py" "# Version exécutable du notebook"
New-File "$root/spark/jobs/retry_dlq_handler.py" "# Gestion retry/DLQ"

New-File "$root/spark/configs/spark_config.yaml" "# Paramètres SparkSession"
New-File "$root/spark/configs/delta_config.yaml" "# Paramètres Delta Lake"

New-File "$root/spark/tests/test_streaming_ingestion.py" "# Test de flux Kafka -> Delta"
New-File "$root/spark/tests/test_data_validation.py" "# Validation JSON schema"

# ===============================================
# Airflow
# ===============================================
New-File "$root/airflow/dags/dag_ingestion_crm.py" "# DAG orchestration ingestion CRM"
New-File "$root/airflow/dags/dag_ingestion_kyc.py" "# DAG batch KYC"
New-File "$root/airflow/dags/dag_monitoring_dlq.py" "# DAG supervision des messages en erreur"

New-File "$root/airflow/plugins/operators/kafka_operator.py" "# Operator Kafka"
New-File "$root/airflow/plugins/operators/spark_submit_operator.py" "# Operator Spark Submit"
New-File "$root/airflow/plugins/operators/vault_secret_operator.py" "# Operator pour récupérer secrets Vault"

New-File "$root/airflow/plugins/sensors/kafka_topic_sensor.py" "# Sensor Kafka topic"

# ===============================================
# Validation
# ===============================================
New-File "$root/validation/schemas/crm_schema.json" "# Schéma de validation CRM"
New-File "$root/validation/schemas/transaction_schema.json" "# Schéma de validation transaction"
New-File "$root/validation/schemas/kyc_schema.json" "# Schéma de validation KYC"

New-File "$root/validation/utils/schema_validator.py" "# Utilitaire de validation JSON/Avro"
New-File "$root/validation/utils/dlq_handler.py" "# Gestion DLQ automatique"
New-File "$root/validation/utils/retry_manager.py" "# Mécanisme de retry"

New-File "$root/validation/tests/test_schema_validator.py" "# Test du validateur de schémas"
New-File "$root/validation/tests/test_dlq_retry.py" "# Test DLQ/retry"

Write-Host ""
Write-Host "🎯 Arborescence complète créée sous : $root/"
