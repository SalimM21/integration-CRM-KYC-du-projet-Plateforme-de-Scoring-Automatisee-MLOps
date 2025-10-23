# Utilitaire de validation JSON/Avro
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schema_validator.py
-------------------
Utilitaire de validation pour les schémas JSON et Avro.
Ce module est utilisé pour vérifier la conformité des messages entrants
avant ingestion dans Kafka, Delta Lake ou Data Warehouse.

Compatible avec :
 - Schémas JSON (kyc_schema.json, crm_schema.json, transaction_schema.json)
 - Schémas Avro (crm_customers.avsc, transactions.avsc)

Auteur : Salim Majide
Date : 2025-10-23
"""

import json
import avro.schema
import avro.io
import io
from jsonschema import validate, ValidationError
from typing import Any, Dict


# =========================
# 🔹 Validation JSON Schema
# =========================
def validate_json(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Valide un dictionnaire JSON selon un schéma JSON.

    Args:
        data (dict): Données à valider
        schema_path (str): Chemin vers le fichier schéma (.json)

    Returns:
        bool: True si valide, sinon lève une exception ValidationError
    """
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        print(f"[❌] Erreur de validation JSON : {e.message}")
        return False
    except FileNotFoundError:
        print(f"[⚠️] Fichier de schéma introuvable : {schema_path}")
        return False


# =========================
# 🔹 Validation Avro Schema
# =========================
def validate_avro(record: Dict[str, Any], schema_path: str) -> bool:
    """
    Valide un enregistrement selon un schéma Avro.

    Args:
        record (dict): Données à valider
        schema_path (str): Chemin vers le schéma Avro (.avsc)

    Returns:
        bool: True si valide, False sinon
    """
    try:
        schema = avro.schema.parse(open(schema_path, "r", encoding="utf-8").read())
        writer = avro.io.DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(record, encoder)
        return True
    except avro.io.AvroTypeException as e:
        print(f"[❌] Erreur de validation Avro : {e}")
        return False
    except Exception as e:
        print(f"[⚠️] Erreur inattendue : {e}")
        return False


# =========================
# 🔹 Fonction générique
# =========================
def validate_message(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Détermine automatiquement le type du schéma (JSON ou Avro)
    et applique la validation correspondante.

    Args:
        data (dict): Données à valider
        schema_path (str): Chemin du schéma

    Returns:
        bool: True si valide, False sinon
    """
    if schema_path.endswith(".json"):
        return validate_json(data, schema_path)
    elif schema_path.endswith(".avsc"):
        return validate_avro(data, schema_path)
    else:
        print(f"[⚠️] Type de schéma non reconnu : {schema_path}")
        return False


# =========================
# 🔹 Exemple d'utilisation
# =========================
if __name__ == "__main__":
    sample_crm = {
        "customer_id": 101,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "created_at": "2025-10-23T10:00:00Z"
    }

    print("=== Test Validation CRM ===")
    result = validate_message(sample_crm, "schemas/json/crm_schema.json")
    print("Résultat :", "✅ Valide" if result else "❌ Invalide")

    sample_txn = {
        "transaction_id": 555,
        "customer_id": 101,
        "amount": 120.5,
        "currency": "USD",
        "timestamp": "2025-10-23T11:00:00Z"
    }

    print("\n=== Test Validation Transaction ===")
    result = validate_message(sample_txn, "schemas/avro/transactions.avsc")
    print("Résultat :", "✅ Valide" if result else "❌ Invalide")
