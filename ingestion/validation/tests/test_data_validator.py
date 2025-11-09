"""
Tests unitaires pour le validateur de données CRM et KYC
"""
import pytest
from validation.data_validator import validate_crm_data, validate_kyc_data, validate_batch

def test_valid_crm_data(valid_crm_data):
    """Test la validation des données CRM valides"""
    result = validate_crm_data(valid_crm_data)
    assert result["is_valid"] is True
    assert result["errors"] is None
    assert "customer_id" in result["data"]

def test_invalid_crm_data(valid_crm_data, invalid_data_samples):
    """Test la validation des données CRM invalides"""
    invalid_data = valid_crm_data.copy()
    invalid_data["email"] = invalid_data_samples["invalid_email"]
    result = validate_crm_data(invalid_data)
    assert result["is_valid"] is False
    assert "email" in str(result["errors"]).lower()

def test_invalid_phone_format(valid_crm_data, invalid_data_samples):
    """Test la validation du format de téléphone invalide"""
    invalid_data = valid_crm_data.copy()
    invalid_data["phone"] = invalid_data_samples["invalid_phone"]
    result = validate_crm_data(invalid_data)
    assert result["is_valid"] is False
    assert "téléphone" in str(result["errors"]).lower()

def test_valid_kyc_data(valid_kyc_data):
    """Test la validation des données KYC valides"""
    result = validate_kyc_data(valid_kyc_data)
    assert result["is_valid"] is True
    assert result["errors"] is None
    assert "customer_id" in result["data"]

def test_invalid_kyc_status(valid_kyc_data, invalid_data_samples):
    """Test la validation d'un statut KYC invalide"""
    invalid_data = valid_kyc_data.copy()
    invalid_data["verification_status"] = invalid_data_samples["invalid_verification_status"]
    result = validate_kyc_data(invalid_data)
    assert result["is_valid"] is False
    assert "statut" in str(result["errors"]).lower()

def test_invalid_risk_level(valid_kyc_data, invalid_data_samples):
    """Test la validation d'un niveau de risque invalide"""
    invalid_data = valid_kyc_data.copy()
    invalid_data["risk_level"] = invalid_data_samples["invalid_risk_level"]
    result = validate_kyc_data(invalid_data)
    assert result["is_valid"] is False
    assert "risque" in str(result["errors"]).lower()

def test_batch_validation_crm(batch_crm_data):
    """Test la validation par lot des données CRM"""
    results = validate_batch("crm", batch_crm_data)
    assert results["total"] == 3
    assert results["valid"] == 3
    assert results["invalid"] == 0
    assert len(results["errors"]) == 0

def test_batch_validation_kyc(batch_kyc_data):
    """Test la validation par lot des données KYC"""
    results = validate_batch("kyc", batch_kyc_data)
    assert results["total"] == 3
    assert results["valid"] == 3
    assert results["invalid"] == 0
    assert len(results["errors"]) == 0

def test_missing_required_fields_crm(valid_crm_data, expected_validation_errors):
    """Test la validation avec des champs requis manquants pour CRM"""
    invalid_data = valid_crm_data.copy()
    del invalid_data["customer_id"]
    result = validate_crm_data(invalid_data)
    assert result["is_valid"] is False
    assert expected_validation_errors["customer_id"] in str(result["errors"]).lower()

def test_missing_required_fields_kyc(valid_kyc_data, expected_validation_errors):
    """Test la validation avec des champs requis manquants pour KYC"""
    invalid_data = valid_kyc_data.copy()
    del invalid_data["verification_status"]
    result = validate_kyc_data(invalid_data)
    assert result["is_valid"] is False
    assert "verification_status" in str(result["errors"]).lower()

def test_multiple_errors_crm(valid_crm_data, invalid_data_samples):
    """Test la validation avec plusieurs erreurs pour CRM"""
    invalid_data = valid_crm_data.copy()
    invalid_data.update({
        "email": invalid_data_samples["invalid_email"],
        "phone": invalid_data_samples["invalid_phone"],
        "customer_id": invalid_data_samples["invalid_customer_id"]
    })
    result = validate_crm_data(invalid_data)
    assert result["is_valid"] is False
    assert len(str(result["errors"]).split(",")) > 2

def test_multiple_errors_kyc(valid_kyc_data, invalid_data_samples):
    """Test la validation avec plusieurs erreurs pour KYC"""
    invalid_data = valid_kyc_data.copy()
    invalid_data.update({
        "verification_status": invalid_data_samples["invalid_verification_status"],
        "risk_level": invalid_data_samples["invalid_risk_level"]
    })
    result = validate_kyc_data(invalid_data)
    assert result["is_valid"] is False
    assert len(str(result["errors"]).split(",")) > 1