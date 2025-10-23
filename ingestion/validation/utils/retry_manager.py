# Mécanisme de retry
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retry_manager.py
----------------
Gestion centralisée du mécanisme de "retry" pour les messages échoués.
Ce module peut être exécuté indépendamment (cron, Airflow, CLI) ou appelé depuis dlq_handler.py.

Fonctions principales :
 - Lecture des messages échoués (DLQ)
 - Validation et tentative de réinjection vers un topic Kafka de retry
 - Archivage après le nombre maximal d’essais

Auteur : Salim Majide
Date : 2025-10-23
"""

import os
import json
import time
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from utils.schema_validator import validate_message


# =========================
# 🔹 Configuration
# =========================
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "localhost:9092")
DLQ_TOPIC = os.getenv("DLQ_TOPIC", "dlq_topic")
RETRY_TOPIC = os.getenv("RETRY_TOPIC", "retry_topic")
MAX_RETRY = int(os.getenv("MAX_RETRY", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 10))  # secondes


# =========================
# 🔹 Producteur Kafka
# =========================
def create_producer():
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        retries=3,
        linger_ms=100,
    )


# =========================
# 🔹 Consommateur Kafka (DLQ)
# =========================
def create_consumer():
    return KafkaConsumer(
        DLQ_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="retry_manager_group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )


# =========================
# 🔹 Gestion du Retry
# =========================
def process_message(msg, producer):
    """
    Traite un message DLQ :
     - Vérifie le schéma
     - Réinjecte vers RETRY_TOPIC si OK
     - Archive si max retry atteint
    """
    data = msg.value
    payload = data.get("payload", {})
    schema_path = data.get("schema_path", "")
    retry_count = data.get("retry_count", 0)

    print(f"[📥] Message reçu depuis DLQ (retry={retry_count}): {data}")

    if validate_message(payload, schema_path):
        if retry_count < MAX_RETRY:
            data["retry_count"] = retry_count + 1
            data["last_retry_at"] = datetime.utcnow().isoformat()

            producer.send(RETRY_TOPIC, value=data)
            print(f"[✅] Message renvoyé vers {RETRY_TOPIC} (retry={retry_count + 1})")
        else:
            archive_failed_message(data, "Nombre max de retry atteint")
    else:
        print("[❌] Validation échouée, message archivé.")
        archive_failed_message(data, "Validation échouée")


# =========================
# 🔹 Archivage des erreurs
# =========================
def archive_failed_message(data, reason):
    """
    Sauvegarde locale (ou S3/Delta) des messages irrécupérables.
    """
    archive_dir = os.getenv("ARCHIVE_DIR", "./archive")
    os.makedirs(archive_dir, exist_ok=True)

    file_path = os.path.join(archive_dir, f"dlq_{int(time.time())}.json")
    record = {
        "data": data,
        "error_reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(f"[📦] Message archivé localement → {file_path}")


# =========================
# 🔹 Boucle principale
# =========================
def run():
    consumer = create_consumer()
    producer = create_producer()

    print(f"[🚀] Retry Manager démarré — Écoute {DLQ_TOPIC}")

    for msg in consumer:
        try:
            process_message(msg, producer)
            time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"[⚠️] Erreur lors du traitement du message : {e}")


# =========================
# 🔹 Exécution directe
# =========================
if __name__ == "__main__":
    run()
