"""
Validation des données CRM et KYC
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

class CRMData(BaseModel):
    """Modèle de validation pour les données CRM"""
    customer_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    address: Optional[str]
    updated_at: datetime

    @validator('phone')
    def validate_phone(cls, v):
        """Valide le format du numéro de téléphone"""
        if v and not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Format de numéro de téléphone invalide')
        return v

    @validator('customer_id')
    def validate_customer_id(cls, v):
        """Valide le format de l'ID client"""
        if not re.match(r'^[A-Za-z0-9]{8,}$', v):
            raise ValueError('Format d\'ID client invalide')
        return v

class KYCData(BaseModel):
    """Modèle de validation pour les données KYC"""
    customer_id: str
    id_type: Optional[str]
    id_number: Optional[str]
    verification_status: str
    risk_level: str
    verified_at: datetime

    @validator('verification_status')
    def validate_verification_status(cls, v):
        """Valide le statut de vérification"""
        valid_statuses = ['pending', 'verified', 'rejected', 'expired']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Statut de vérification invalide. Doit être l\'un de: {valid_statuses}')
        return v.lower()

    @validator('risk_level')
    def validate_risk_level(cls, v):
        """Valide le niveau de risque"""
        valid_levels = ['low', 'medium', 'high']
        if v.lower() not in valid_levels:
            raise ValueError(f'Niveau de risque invalide. Doit être l\'un de: {valid_levels}')
        return v.lower()

def validate_crm_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide les données CRM
    """
    try:
        validated_data = CRMData(**data)
        return {
            'is_valid': True,
            'data': validated_data.dict(),
            'errors': None
        }
    except Exception as e:
        return {
            'is_valid': False,
            'data': None,
            'errors': str(e)
        }

def validate_kyc_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide les données KYC
    """
    try:
        validated_data = KYCData(**data)
        return {
            'is_valid': True,
            'data': validated_data.dict(),
            'errors': None
        }
    except Exception as e:
        return {
            'is_valid': False,
            'data': None,
            'errors': str(e)
        }

def validate_batch(data_type: str, batch_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valide un lot de données
    """
    results = {
        'total': len(batch_data),
        'valid': 0,
        'invalid': 0,
        'errors': []
    }

    validator = validate_crm_data if data_type == 'crm' else validate_kyc_data

    for item in batch_data:
        validation_result = validator(item)
        if validation_result['is_valid']:
            results['valid'] += 1
        else:
            results['invalid'] += 1
            results['errors'].append({
                'data': item,
                'error': validation_result['errors']
            })

    return results