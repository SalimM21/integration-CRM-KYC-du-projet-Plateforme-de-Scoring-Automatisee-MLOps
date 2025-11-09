# Ajout de cas de test pour la validation des données
import pytest
from datetime import datetime, timedelta
from validation.data_validator import validate_crm_data, validate_kyc_data, validate_batch

def test_date_validation_crm(valid_crm_data, invalid_data_samples):
    """Test la validation des dates pour CRM"""
    invalid_data = valid_crm_data.copy()
    invalid_data["updated_at"] = invalid_data_samples["invalid_date"]
    result = validate_crm_data(invalid_data)
    assert result["is_valid"] is False
    assert "date" in str(result["errors"]).lower()

def test_date_validation_kyc(valid_kyc_data, invalid_data_samples):
    """Test la validation des dates pour KYC"""
    invalid_data = valid_kyc_data.copy()
    invalid_data["verified_at"] = invalid_data_samples["invalid_date"]
    result = validate_kyc_data(invalid_data)
    assert result["is_valid"] is False
    assert "date" in str(result["errors"]).lower()

def test_empty_batch():
    """Test la validation d'un lot vide"""
    results = validate_batch("crm", [])
    assert results["total"] == 0
    assert results["valid"] == 0
    assert results["invalid"] == 0
    assert len(results["errors"]) == 0

def test_large_batch_crm(valid_crm_data):
    """Test la validation d'un grand lot de données CRM"""
    # Création d'un lot de 100 éléments
    large_batch = []
    for i in range(100):
        data = valid_crm_data.copy()
        data["customer_id"] = f"CUST{i:05d}"
        data["email"] = f"user{i}@example.com"
        data["updated_at"] = datetime.now() - timedelta(days=i)
        large_batch.append(data)
    
    results = validate_batch("crm", large_batch)
    assert results["total"] == 100
    assert results["valid"] == 100
    assert results["invalid"] == 0

def test_mixed_valid_invalid_batch(valid_crm_data, invalid_data_samples):
    """Test la validation d'un lot avec données valides et invalides mélangées"""
    batch_data = []
    
    # Ajout de données valides
    for i in range(3):
        data = valid_crm_data.copy()
        data["customer_id"] = f"CUST{i:05d}"
        batch_data.append(data)
    
    # Ajout de données invalides
    invalid_data = valid_crm_data.copy()
    invalid_data["email"] = invalid_data_samples["invalid_email"]
    batch_data.append(invalid_data)
    
    invalid_data = valid_crm_data.copy()
    invalid_data["phone"] = invalid_data_samples["invalid_phone"]
    batch_data.append(invalid_data)
    
    results = validate_batch("crm", batch_data)
    assert results["total"] == 5
    assert results["valid"] == 3
    assert results["invalid"] == 2
    assert len(results["errors"]) == 2

def test_optional_fields_crm(valid_crm_data):
    """Test la validation avec des champs optionnels manquants pour CRM"""
    data = valid_crm_data.copy()
    optional_fields = ["first_name", "last_name", "address", "phone"]
    
    for field in optional_fields:
        test_data = data.copy()
        del test_data[field]
        result = validate_crm_data(test_data)
        assert result["is_valid"] is True, f"Le champ {field} devrait être optionnel"

def test_optional_fields_kyc(valid_kyc_data):
    """Test la validation avec des champs optionnels manquants pour KYC"""
    data = valid_kyc_data.copy()
    optional_fields = ["id_type", "id_number"]
    
    for field in optional_fields:
        test_data = data.copy()
        del test_data[field]
        result = validate_kyc_data(test_data)
        assert result["is_valid"] is True, f"Le champ {field} devrait être optionnel"

def test_whitespace_validation(valid_crm_data):
    """Test la validation avec des espaces superflus"""
    data = valid_crm_data.copy()
    data["first_name"] = "  Jean  "
    data["last_name"] = "Dupont  "
    data["email"] = " jean.dupont@example.com "
    
    result = validate_crm_data(data)
    assert result["is_valid"] is True
    assert result["data"]["first_name"] == "Jean"
    assert result["data"]["last_name"] == "Dupont"
    assert result["data"]["email"] == "jean.dupont@example.com"