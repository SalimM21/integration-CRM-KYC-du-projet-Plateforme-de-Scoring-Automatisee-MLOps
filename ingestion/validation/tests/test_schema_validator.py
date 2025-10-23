# Test du validateur de schémas
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_schema_validator.py
------------------------
Tests unitaires pour le module schema_validator.py

Objectif :
- Vérifier la validation de schémas JSON et Avro
- Gérer les cas d’erreur (mauvais format, schéma absent, données invalides)
- Confirmer la compatibilité avec les messages utilisés dans Kafka

Auteur : Salim Majide
Date : 2025-10-23
"""

import os
import json
import pytest
from utils.schema_validator import validate_message, load_json_schema, load_avro_schema


# =========================
# 🔧 Configuration des chemins
# =========================
BASE_DIR = os.path.dirname(__file__)
SCHEMA_DIR = os.path.join(BASE_DIR, "schemas")

os.makedirs(SCHEMA_DIR, exist_ok=True)

# Schéma JSON de test (CRM)
TEST_JSON_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "crm_schema.json")
TEST_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_id": {"type": "string"},
        "email": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["customer_id", "email"]
}

# Schéma Avro de test (transactions)
TEST_AVRO_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "transactions.avsc")
TEST_AVRO_SCHEMA = {
    "type": "record",
    "name": "Transaction",
    "fields": [
        {"name": "transaction_id", "type": "string"},
        {"name": "amount", "type": "float"},
        {"name": "status", "type": "string"}
    ]
}


# =========================
# 🔹 Setup : Création des fichiers de test
# =========================
@pytest.fixture(scope="module", autouse=True)
def setup_schemas():
    """Créer les schémas de test localement avant exécution."""
    with open(TEST_JSON_SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(TEST_JSON_SCHEMA, f, indent=2)

    with open(TEST_AVRO_SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(TEST_AVRO_SCHEMA, f, indent=2)

    yield  # exécution des tests

    os.remove(TEST_JSON_SCHEMA_PATH)
    os.remove(TEST_AVRO_SCHEMA_PATH)


# =========================
# 🔹 Tests JSON Schema
# =========================
def test_validate_message_json_valid():
    """✅ Test : message JSON conforme au schéma."""
    msg = {"customer_id": "C123", "email": "test@example.com", "age": 30}
    assert validate_message(msg, TEST_JSON_SCHEMA_PATH) is True


def test_validate_message_json_invalid_missing_field():
    """❌ Test : champ manquant (email)."""
    msg = {"customer_id": "C123"}
    assert validate_message(msg, TEST_JSON_SCHEMA_PATH) is False


def test_load_json_schema_ok():
    """✅ Test : chargement d’un schéma JSON valide."""
    schema = load_json_schema(TEST_JSON_SCHEMA_PATH)
    assert schema["type"] == "object"


def test_load_json_schema_not_found():
    """⚠️ Test : schéma JSON manquant."""
    with pytest.raises(FileNotFoundError):
        load_json_schema("schemas/inexistant.json")


# =========================
# 🔹 Tests Avro Schema
# =========================
def test_load_avro_schema_ok():
    """✅ Test : chargement schéma Avro valide."""
    schema = load_avro_schema(TEST_AVRO_SCHEMA_PATH)
    assert schema["name"] == "Transaction"


def test_validate_message_avro_valid(monkeypatch):
    """✅ Test : message Avro valide."""
    msg = {"transaction_id": "TX1001", "amount": 250.0, "status": "OK"}

    # Mock interne : simulateur de validation Avro (pour pytest sans fastavro)
    monkeypatch.setattr("utils.schema_validator.validate_avro_message", lambda m, s: True)
    assert validate_message(msg, TEST_AVRO_SCHEMA_PATH) is True


def test_validate_message_avro_invalid(monkeypatch):
    """❌ Test : message Avro invalide."""
    msg = {"transaction_id": 1234, "amount": "invalid", "status": 50}

    monkeypatch.setattr("utils.schema_validator.validate_avro_message", lambda m, s: False)
    assert validate_message(msg, TEST_AVRO_SCHEMA_PATH) is False


# =========================
# 🔹 Tests généraux
# =========================
def test_validate_message_schema_not_found():
    """⚠️ Test : chemin de schéma inexistant."""
    msg = {"x": "y"}
    assert validate_message(msg, "schemas/unknown.avsc") is False


def test_validate_message_empty_payload():
    """⚠️ Test : payload vide."""
    assert validate_message({}, TEST_JSON_SCHEMA_PATH) is False


def test_invalid_schema_type(monkeypatch):
    """⚠️ Test : type de fichier non supporté."""
    monkeypatch.setattr("utils.schema_validator.detect_schema_type", lambda p: "unsupported")
    msg = {"key": "value"}
    assert validate_message(msg, TEST_JSON_SCHEMA_PATH) is False
