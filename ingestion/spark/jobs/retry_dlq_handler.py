# Gestion retry/DLQ
#!/usr/bin/env python3
"""
Retry & DLQ Handler pour Kafka
Gestion des messages échoués et envoi vers Dead Letter Queue
"""

from kafka import KafkaConsumer, KafkaProducer
import json
import time

# -----------------------------
# Configuration Kafka
# -----------------------------
KAFKA_BOOTSTRAP = "kafka-cluster-kafka-bootstrap:9092"
SOURCE_TOPIC = "transactions"
DLQ_TOPIC = "transactions_dlq"
GROUP_ID = "retry_handler_group"
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

# -----------------------------
# Kafka Producer pour DLQ
# -----------------------------
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# -----------------------------
# Kafka Consumer
# -----------------------------
consumer = KafkaConsumer(
    SOURCE_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    group_id=GROUP_ID,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=False
)

# -----------------------------
# Fonction de traitement
# -----------------------------
def process_message(msg):
    """
    Traitement de message
    Retourne True si succès, False si échec
    """
    try:
        # Exemple : traitement métier
        # Ici on simule une erreur pour testing
        if "fail" in msg.get("transaction_id", ""):
            raise Exception("Traitement échoué")
        print(f"✅ Message traité : {msg['transaction_id']}")
        return True
    except Exception as e:
        print(f"❌ Erreur traitement message {msg.get('transaction_id')}: {e}")
        return False

# -----------------------------
# Loop principal avec retry / DLQ
# -----------------------------
for record in consumer:
    msg = record.value
    retries = 0
    success = False

    while retries < MAX_RETRIES and not success:
        success = process_message(msg)
        if not success:
            retries += 1
            print(f"Retry {retries}/{MAX_RETRIES} pour {msg.get('transaction_id')}")
            time.sleep(RETRY_DELAY_SEC)

    if not success:
        print(f"📥 Envoi message vers DLQ: {msg.get('transaction_id')}")
        producer.send(DLQ_TOPIC, msg)

    # Commit offset après succès ou envoi DLQ
    consumer.commit()
