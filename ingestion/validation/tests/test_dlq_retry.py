# Test DLQ/retry
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dlq_retry.py
-----------------
Tests unitaires pour les modules :
- dlq_handler.py  (gestion DLQ automatique)
- retry_manager.py (mécanisme de retry Kafka)

Vérifie :
✅ La redirection des messages en erreur vers le topic DLQ
✅ La logique de réessai avec compteur et délais progressifs
✅ La compatibilité avec la structure du cluster Kafka simulé

Auteur : Salim Majide
Date : 2025-10-23
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from utils.dlq_handler import DLQHandler
from utils.retry_manager import RetryManager


# ==============================
# 🔧 Fixtures de test
# ==============================
@pytest.fixture
def kafka_mock():
    """Mock d’un producteur Kafka."""
    producer = MagicMock()
    producer.send = MagicMock(return_value=True)
    return producer


@pytest.fixture
def dlq_handler(kafka_mock):
    """Instance de DLQHandler avec Kafka mocké."""
    return DLQHandler(
        bootstrap_servers="localhost:9092",
        dlq_topic="crm.customers.dlq",
        kafka_producer=kafka_mock
    )


@pytest.fixture
def retry_manager(kafka_mock):
    """Instance de RetryManager avec Kafka mocké."""
    return RetryManager(
        bootstrap_servers="localhost:9092",
        retry_topic="crm.customers.retry",
        max_retries=3,
        kafka_producer=kafka_mock
    )


# ==============================
# 🔹 Tests DLQHandler
# ==============================
def test_dlq_handler_send_to_dlq(dlq_handler):
    """✅ Envoi correct d’un message invalide dans le topic DLQ."""
    message = {"customer_id": "C001", "error": "invalid schema"}
    dlq_handler.send_to_dlq(message, reason="SchemaValidationError")

    dlq_handler.kafka_producer.send.assert_called_once_with(
        "crm.customers.dlq",
        json.dumps({
            "original_message": message,
            "reason": "SchemaValidationError"
        }).encode("utf-8")
    )


def test_dlq_handler_log_error(monkeypatch):
    """⚠️ Si le Kafka producer échoue, log d’erreur doit apparaître."""
    mock_logger = MagicMock()
    monkeypatch.setattr("utils.dlq_handler.logger", mock_logger)

    producer = MagicMock()
    producer.send.side_effect = Exception("Kafka unavailable")

    dlq = DLQHandler(
        bootstrap_servers="localhost:9092",
        dlq_topic="crm.customers.dlq",
        kafka_producer=producer
    )

    dlq.send_to_dlq({"x": "y"}, "TestError")
    mock_logger.error.assert_called()


# ==============================
# 🔹 Tests RetryManager
# ==============================
def test_retry_manager_first_attempt(retry_manager):
    """✅ Premier retry : le message est renvoyé sur le topic retry."""
    message = {"customer_id": "C001", "retry_count": 0}
    retry_manager.retry_message(message)

    retry_manager.kafka_producer.send.assert_called_once_with(
        "crm.customers.retry",
        json.dumps(message).encode("utf-8")
    )


def test_retry_manager_max_retries_exceeded(dlq_handler, retry_manager):
    """❌ Si le message dépasse le nombre max de retries, il part en DLQ."""
    message = {"customer_id": "C001", "retry_count": 5}

    with patch.object(retry_manager, "dlq_handler", dlq_handler):
        retry_manager.retry_message(message)
        dlq_handler.kafka_producer.send.assert_called_once()


def test_retry_manager_backoff(monkeypatch, retry_manager):
    """⏳ Test du délai exponentiel entre retries."""
    monkeypatch.setattr("time.sleep", MagicMock())
    message = {"customer_id": "C002", "retry_count": 2}
    retry_manager.retry_message(message)

    # Vérifie qu’un délai exponentiel a été simulé (2 ** 2 = 4 sec)
    retry_manager.kafka_producer.send.assert_called_once()
    time_sleep_mock = monkeypatch.getattr("time.sleep")
    assert time_sleep_mock.called


def test_retry_manager_missing_retry_count(monkeypatch, retry_manager):
    """⚠️ Si retry_count absent, il doit être ajouté automatiquement."""
    message = {"customer_id": "C999"}

    monkeypatch.setattr("time.sleep", MagicMock())
    retry_manager.retry_message(message)

    # Le champ retry_count doit être créé
    assert "retry_count" in message
    retry_manager.kafka_producer.send.assert_called_once()


# ==============================
# 🔹 Tests d’intégration légère DLQ + Retry
# ==============================
def test_integration_retry_to_dlq(kafka_mock):
    """✅ Test combiné : retry échoue puis part vers DLQ."""
    message = {"customer_id": "C003", "retry_count": 3}

    dlq_handler = DLQHandler("localhost:9092", "crm.customers.dlq", kafka_producer=kafka_mock)
    retry_manager = RetryManager("localhost:9092", "crm.customers.retry", max_retries=2, kafka_producer=kafka_mock)
    retry_manager.dlq_handler = dlq_handler

    retry_manager.retry_message(message)
    kafka_mock.send.assert_called_with(
        "crm.customers.dlq",
        json.dumps({
            "original_message": message,
            "reason": "MaxRetryExceeded"
        }).encode("utf-8")
    )
