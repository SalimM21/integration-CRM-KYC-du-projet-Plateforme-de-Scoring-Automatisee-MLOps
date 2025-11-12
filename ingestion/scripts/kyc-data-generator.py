#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kyc-data-generator.py
---------------------
Générateur de données KYC pour simuler un connecteur source.
Ce script génère des données KYC fictives et les publie sur le topic Kafka kyc-responses.

Auteur : Kilo Code
Date : 2025-11-12
"""

import os
import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

# Configuration
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "my-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092")
TOPIC = "kyc-responses"
INTERVAL = int(os.getenv("INTERVAL", 30))  # secondes

def create_producer():
    """Créer un producteur Kafka."""
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        retries=3,
        linger_ms=100,
    )

def generate_kyc_data():
    """Générer des données KYC fictives."""
    customer_id = f"CUST{random.randint(1000, 9999)}"

    kyc_data = {
        "customer_id": customer_id,
        "kyc_status": random.choice(["VERIFIED", "PENDING", "REJECTED"]),
        "risk_score": round(random.uniform(0.1, 0.9), 2),
        "documents_verified": random.choice([True, False]),
        "verification_date": int(time.time() * 1000),
        "personal_info": {
            "first_name": random.choice(["Alice", "Bob", "Charlie", "Diana", "Eve"]),
            "last_name": random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"]),
            "date_of_birth": f"{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "nationality": random.choice(["FR", "DE", "IT", "ES", "GB"]),
        },
        "address": {
            "street": f"{random.randint(1, 999)} {random.choice(['Rue', 'Avenue', 'Boulevard'])} {random.choice(['de la Paix', 'Victor Hugo', 'des Champs'])}",
            "city": random.choice(["Paris", "Lyon", "Marseille", "Toulouse", "Nice"]),
            "postal_code": f"{random.randint(10000, 99999)}",
            "country": "FR"
        },
        "compliance_flags": {
            "pep_check": random.choice([True, False]),
            "sanctions_check": random.choice([True, False]),
            "aml_risk": random.choice(["LOW", "MEDIUM", "HIGH"])
        },
        "timestamp": int(time.time() * 1000)
    }

    return kyc_data

def main():
    """Fonction principale."""
    print(f"[🚀] Démarrage du générateur KYC - Topic: {TOPIC}")

    producer = create_producer()

    try:
        while True:
            # Générer et publier des données KYC
            kyc_data = generate_kyc_data()

            # Publier sur Kafka
            future = producer.send(TOPIC, value=kyc_data)
            record_metadata = future.get(timeout=10)

            print(f"[✅] Données KYC publiées - Customer: {kyc_data['customer_id']}, Status: {kyc_data['kyc_status']}")

            # Attendre avant la prochaine génération
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("[🛑] Arrêt du générateur KYC")
    except Exception as e:
        print(f"[❌] Erreur: {e}")
    finally:
        producer.close()

if __name__ == "__main__":
    main()