# ===============================================
# Policy Vault pour File Rouge - accès secrets
# ===============================================

# Namespace / chemin racine des secrets
path "secret/data/file-rouge/*" {
  capabilities = ["read", "list"]
}

# Exemple pour KafkaUser credentials
path "secret/data/file-rouge/kafka-user" {
  capabilities = ["read"]
}

# Exemple pour KYC API secrets
path "secret/data/file-rouge/kyc-api" {
  capabilities = ["read"]
}

# Exemple pour MinIO/S3 access keys
path "secret/data/file-rouge/minio" {
  capabilities = ["read"]
}

# Exemple pour DWH / JDBC credentials
path "secret/data/file-rouge/dwh" {
  capabilities = ["read"]
}

# Optionnel : logs ou rotation keys
path "secret/data/file-rouge/logs/*" {
  capabilities = ["read"]
}

# Interdiction totale d'écriture / suppression pour la majorité
path "secret/data/file-rouge/*" {
  capabilities = ["deny"]
}
