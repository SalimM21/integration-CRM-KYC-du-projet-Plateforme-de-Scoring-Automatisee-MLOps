# Operator pour récupérer secrets Vault
#!/usr/bin/env python3
"""
Module Vault Secret Operator
Permet de récupérer et gérer les secrets depuis HashiCorp Vault
"""

import hvac
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VaultSecretOperator")

# -----------------------------
# Configuration globale
# -----------------------------
VAULT_URL = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")  # idéalement via Kubernetes Secret ou CI/CD
VAULT_NAMESPACE = os.getenv("VAULT_NAMESPACE", None)

# -----------------------------
# Créer le client Vault
# -----------------------------
def get_vault_client():
    client = hvac.Client(url=VAULT_URL, token=VAULT_TOKEN, namespace=VAULT_NAMESPACE)
    if client.is_authenticated():
        logger.info("✅ Authentifié auprès de Vault")
    else:
        logger.error("❌ Échec authentification Vault")
        raise Exception("Vault authentication failed")
    return client

# -----------------------------
# Récupérer un secret
# -----------------------------
def get_secret(secret_path, key=None):
    """
    :param secret_path: chemin du secret dans Vault
    :param key: clé spécifique dans le secret (optionnel)
    """
    client = get_vault_client()
    try:
        secret_response = client.secrets.kv.v2.read_secret_version(path=secret_path)
        data = secret_response['data']['data']
        if key:
            return data.get(key)
        return data
    except Exception as e:
        logger.error(f"❌ Impossible de récupérer le secret {secret_path} : {e}")
        return None

# -----------------------------
# Écrire / mettre à jour un secret
# -----------------------------
def write_secret(secret_path, secret_data: dict):
    """
    :param secret_path: chemin du secret dans Vault
    :param secret_data: dict de clés/valeurs à stocker
    """
    client = get_vault_client()
    try:
        client.secrets.kv.v2.create_or_update_secret(path=secret_path, secret=secret_data)
        logger.info(f"✅ Secret écrit dans Vault : {secret_path}")
    except Exception as e:
        logger.error(f"❌ Impossible d'écrire le secret {secret_path} : {e}")

# -----------------------------
# Exemple d'utilisation
# -----------------------------
if __name__ == "__main__":
    # Lecture d'un secret existant
    db_creds = get_secret("file_rouge/datawarehouse", key="password")
    print(f"Mot de passe DB récupéré : {db_creds}")

    # Écriture d'un secret
    write_secret("file_rouge/test_secret", {"username": "testuser", "password": "testpass"})
