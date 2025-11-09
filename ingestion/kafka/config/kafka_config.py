"""
Configuration Kafka pour l'ingestion des données
"""
from typing import Dict, Any

KAFKA_CONFIG: Dict[str, Any] = {
    'bootstrap.servers': 'kafka:9092',
    'client.id': 'crm_kyc_producer',
    'acks': 'all',
    'retries': 3,
    'retry.backoff.ms': 1000,
    'batch.size': 16384,
    'linger.ms': 100,
    'max.request.size': 1048576,
    'compression.type': 'gzip'
}

KAFKA_TOPICS = {
    'crm_updates': 'crm_updates_topic',
    'kyc_updates': 'kyc_updates_topic',
    'integrated_updates': 'crm_kyc_updates'
}

SCHEMA_REGISTRY_CONFIG = {
    'url': 'http://schema-registry:8081',
    'auto.register.schemas': True
}

# Schéma Avro pour les messages CRM
CRM_SCHEMA = {
    "type": "record",
    "name": "CRMUpdate",
    "fields": [
        {"name": "customer_id", "type": "string"},
        {"name": "first_name", "type": ["null", "string"]},
        {"name": "last_name", "type": ["null", "string"]},
        {"name": "email", "type": ["null", "string"]},
        {"name": "phone", "type": ["null", "string"]},
        {"name": "address", "type": ["null", "string"]},
        {"name": "updated_at", "type": "long", "logicalType": "timestamp-millis"}
    ]
}

# Schéma Avro pour les messages KYC
KYC_SCHEMA = {
    "type": "record",
    "name": "KYCUpdate",
    "fields": [
        {"name": "customer_id", "type": "string"},
        {"name": "id_type", "type": ["null", "string"]},
        {"name": "id_number", "type": ["null", "string"]},
        {"name": "verification_status", "type": "string"},
        {"name": "risk_level", "type": "string"},
        {"name": "verified_at", "type": "long", "logicalType": "timestamp-millis"}
    ]
}

# Configuration des consommateurs
CONSUMER_CONFIG = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'crm_kyc_consumer_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,
    'max.poll.interval.ms': 300000,
    'session.timeout.ms': 30000
}