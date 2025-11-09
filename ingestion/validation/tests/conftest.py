"""
Fixtures de test pour la validation des données CRM et KYC
"""
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def valid_crm_data():
    """Fixture pour des données CRM valides"""
    return {
        "customer_id": "CUST12345",
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "phone": "+33612345678",
        "address": "123 Rue de Paris",
        "updated_at": datetime.now()
    }

@pytest.fixture
def valid_kyc_data():
    """Fixture pour des données KYC valides"""
    return {
        "customer_id": "CUST12345",
        "id_type": "passport",
        "id_number": "PAS123456",
        "verification_status": "verified",
        "risk_level": "low",
        "verified_at": datetime.now()
    }

@pytest.fixture
def batch_crm_data(valid_crm_data):
    """Fixture pour un lot de données CRM"""
    return [
        valid_crm_data,
        {
            **valid_crm_data,
            "customer_id": "CUST67890",
            "email": "marie.martin@example.com",
            "updated_at": datetime.now() - timedelta(days=1)
        },
        {
            **valid_crm_data,
            "customer_id": "CUST11111",
            "email": "pierre.durand@example.com",
            "updated_at": datetime.now() - timedelta(days=2)
        }
    ]

@pytest.fixture
def batch_kyc_data(valid_kyc_data):
    """Fixture pour un lot de données KYC"""
    return [
        valid_kyc_data,
        {
            **valid_kyc_data,
            "customer_id": "CUST67890",
            "verification_status": "pending",
            "risk_level": "medium",
            "verified_at": datetime.now() - timedelta(days=1)
        },
        {
            **valid_kyc_data,
            "customer_id": "CUST11111",
            "verification_status": "rejected",
            "risk_level": "high",
            "verified_at": datetime.now() - timedelta(days=2)
        }
    ]

@pytest.fixture
def invalid_data_samples():
    """Fixture pour différents types de données invalides"""
    return {
        "invalid_email": "not_an_email",
        "invalid_phone": "123",
        "invalid_customer_id": "12",
        "invalid_verification_status": "unknown",
        "invalid_risk_level": "extreme",
        "invalid_date": "not_a_date"
    }

@pytest.fixture
def expected_validation_errors():
    """Fixture pour les messages d'erreur attendus"""
    return {
        "email": "email",
        "phone": "téléphone",
        "customer_id": "client",
        "verification_status": "statut",
        "risk_level": "risque"
    }