# Operator Kafka
#!/usr/bin/env python3
"""
Module Kafka Operator
Fonctions pour produire, consommer et superviser les topics Kafka
"""

from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaOperator")

# -----------------------------
# Configuration globale
# -----------------------------
KAFKA_BOOTSTRAP = "kafka-cluster-kafka-bootstrap:9092"

# -----------------------------
# Créer un topic Kafka
# -----------------------------
def create_topic(topic_name, num_partitions=3, replication_factor=1):
    admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
    topic_list = [NewTopic(name=topic_name,
                           num_partitions=num_partitions,
                           replication_factor=replication_factor)]
    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        logger.info(f"✅ Topic créé : {topic_name}")
    except Exception as e:
        logger.error(f"❌ Erreur création topic {topic_name} : {e}")
    finally:
        admin_client.close()

# -----------------------------
# Envoyer un message Kafka
# -----------------------------
def send_message(topic, message: dict):
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    try:
        producer.send(topic, value=message)
        producer.flush()
        logger.info(f"✅ Message envoyé sur {topic}")
    except Exception as e:
        logger.error(f"❌ Erreur envoi message sur {topic} : {e}")
    finally:
        producer.close()

# -----------------------------
# Consommer les messages Kafka
# -----------------------------
def consume_messages(topic, group_id="file_rouge_group", max_messages=10):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    messages = []
    try:
        for i, msg in enumerate(consumer):
            messages.append(msg.value)
            if i + 1 >= max_messages:
                break
        logger.info(f"✅ {len(messages)} messages consommés depuis {topic}")
    except Exception as e:
        logger.error(f"❌ Erreur consommation topic {topic} : {e}")
    finally:
        consumer.close()
    return messages

# -----------------------------
# Vérifier existence d’un topic
# -----------------------------
def list_topics():
    admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
    try:
        topics = admin_client.list_topics()
        logger.info(f"📜 Topics existants : {topics}")
        return topics
    except Exception as e:
        logger.error(f"❌ Erreur liste topics : {e}")
        return []
    finally:
        admin_client.close()


# -----------------------------
# Exemple d'utilisation
# -----------------------------
if __name__ == "__main__":
    create_topic("test_topic")
    send_message("test_topic", {"id": 1, "name": "Alice"})
    msgs = consume_messages("test_topic", max_messages=5)
    print(msgs)
    list_topics()
