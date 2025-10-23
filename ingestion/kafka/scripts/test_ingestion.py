#!/usr/bin/env python3
"""
Test d’ingestion Kafka (latence et volumétrie) pour le pipeline CRM / Transactions
"""

import time
import json
from kafka import KafkaProducer, KafkaConsumer
import pytest

# -----------------------------
# Configuration Kafka
# -----------------------------
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"  # ou kafka-cluster-kafka-bootstrap:9092
TOPIC = "crm_customers"
TEST_MESSAGES = 100  # Nombre de messages à produire pour le test

# -----------------------------
# Fixtures pytest
# -----------------------------
@pytest.fixture(scope="module")
def producer():
    p = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    yield p
    p.close()

@pytest.fixture(scope="module")
def consumer():
    c = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="test_ingestion_group",
        value_deserializer=lambda v: json.loads(v.decode("utf-8"))
    )
    yield c
    c.close()

# -----------------------------
# Test de latence
# -----------------------------
def test_latency(producer, consumer):
    timestamps = []
    
    # Produire les messages
    for i in range(TEST_MESSAGES):
        msg = {"id": f"test_{i}", "created_at": int(time.time() * 1000)}
        producer.send(TOPIC, value=msg)
        timestamps.append(msg["created_at"])
    
    producer.flush()
    
    # Consommer et calculer la latence
    consumed_count = 0
    latencies = []
    start_time = time.time()
    
    for message in consumer:
        sent_ts = message.value["created_at"]
        latency_ms = int(time.time() * 1000) - sent_ts
        latencies.append(latency_ms)
        consumed_count += 1
        
        if consumed_count >= TEST_MESSAGES:
            break
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"✅ Messages ingérés: {consumed_count}")
    print(f"✅ Latence moyenne: {avg_latency:.2f} ms")
    
    # Assertions simples
    assert consumed_count == TEST_MESSAGES, "Tous les messages n'ont pas été ingérés"
    assert avg_latency < 5000, "Latence trop élevée (>5s)"

# -----------------------------
# Test volumétrie
# -----------------------------
def test_volumetry(producer, consumer):
    # Produire un lot de messages
    for i in range(TEST_MESSAGES):
        msg = {"id": f"vol_test_{i}", "created_at": int(time.time() * 1000)}
        producer.send(TOPIC, value=msg)
    
    producer.flush()
    
    # Consommer et compter
    count = 0
    for message in consumer:
        count += 1
        if count >= TEST_MESSAGES:
            break
    
    print(f"✅ Volumétrie test: {count} messages ingérés")
    assert count == TEST_MESSAGES, "Mismatch dans le nombre de messages ingérés"
