# Gestion DLQ automatique
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dlq_handler.py
--------------
Gestion automatisée de la Dead Letter Queue (DLQ).
Ce module écoute les topics DLQ (Dead Letter Queue), analyse les erreurs,
tente un retry automatique (si applicable), et archive les messages invalides
dans un stockage externe (Delta Lake, S3, MinIO, ou base de logs).

Composants principaux :
 - Lecture Kafka (consumer)
 - Tentative de reprocessing (avec validate_message)
 - Archivage des erreurs dans S3 ou Delta Lake

Auteur : Salim Majide
Date : 2025-10-23
"""

import os
import json
import time
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from utils.schema_validator import validate_message
from pyspark.sql import SparkSession


# =========================
# 🔹 Configuration globale
# =========================
DLQ_TOPIC = os.getenv("DLQ_TOPIC", "dlq_topic")
RETRY_TOPIC = os.getenv("RETRY_TOPIC", "retry_topic")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "localhost:9092")
ARCHIVE_PATH = os.getenv("ARCHIVE_PATH", "s3a://data-lake/dlq_archive/")

MAX_RETRY = int(os.getenv("MAX_RETRY", 3))
RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", 5))  # secondes


# =========================
# 🔹 Spark Session (optionnel)
# =========================
def get_spark_session(app_name="DLQ_Handler"):
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "minio"))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "minio123"))
        .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://localhost:9000"))
        .getOrCreate()
    )


# =========================
# 🔹 Gestion DLQ
# =========================
class DLQHandler:
    def __init__(self):
        self.consumer = KafkaConsumer(
            DLQ_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )

        self.producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

        self.spark = get_spark_session()
        print(f"[🔧] DLQHandler initialisé — Écoute sur le topic : {DLQ_TOPIC}")

    def process_message(self, msg):
        """Traite un message de la DLQ."""
        data = msg.value
        retry_count = data.get("retry_count", 0)
        schema_path = data.get("schema_path", "")

        print(f"[📥] Message reçu avec retry_count={retry_count} : {data}")

        if validate_message(data.get("payload", {}), schema_path):
            # Si validation OK => renvoi vers topic de retry
            if retry_count < MAX_RETRY:
                data["retry_count"] = retry_count + 1
                self.producer.send(RETRY_TOPIC, value=data)
                print(f"[✅] Message revalidé et renvoyé vers {RETRY_TOPIC}")
            else:
                self.archive_message(data, reason="Max retry atteint")
        else:
            print(f"[❌] Message invalide : {data}")
            self.archive_message(data, reason="Validation échouée")

    def archive_message(self, data, reason):
        """Archive un message DLQ vers Delta Lake / S3."""
        df = self.spark.createDataFrame(
            [(json.dumps(data), reason, datetime.utcnow().isoformat())],
            ["message", "error_reason", "archived_at"]
        )
        df.write.mode("append").format("delta").save(ARCHIVE_PATH)
        print(f"[📦] Message archivé dans {ARCHIVE_PATH} ({reason})")

    def run(self):
        """Boucle principale d'écoute."""
        print("[🚀] Démarrage du DLQHandler...")
        for msg in self.consumer:
            try:
                self.process_message(msg)
                time.sleep(RETRY_INTERVAL)
            except Exception as e:
                print(f"[⚠️] Erreur lors du traitement du message : {e}")


# =========================
# 🔹 Exécution directe
# =========================
if __name__ == "__main__":
    handler = DLQHandler()
    handler.run()
