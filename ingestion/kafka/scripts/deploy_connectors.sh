#!/bin/bash
# ==========================================
# Script d’automatisation déploiement Kafka Connect
# ==========================================

# Charger les secrets
if [ -f "./secrets.env" ]; then
  export $(grep -v '^#' ./secrets.env | xargs)
else
  echo "⚠️  secrets.env introuvable !"
  exit 1
fi

# URL Kafka Connect REST
CONNECT_URL="${CONNECT_URL:-http://connect-worker-1:8083}"

# Liste des fichiers connecteurs JSON
CONNECTORS_JSON=(
  "debezium-crm-source.json"
  "jdbc-sink-dwh.json"
  "s3-sink-minio.json"
  "kyc-api-source.json"
)

# Fonction pour déployer un connecteur
deploy_connector() {
  local file=$1
  local name=$(jq -r '.name' "$file")
  echo "Déploiement du connecteur: $name"

  # Vérifier si le connecteur existe déjà
  if curl -s -o /dev/null -w "%{http_code}" "$CONNECT_URL/connectors/$name" | grep -q "200"; then
    echo "Connecteur $name existe déjà, update en cours..."
    curl -s -X PUT -H "Content-Type: application/json" \
         --data @"$file" \
         "$CONNECT_URL/connectors/$name/config" | jq
  else
    curl -s -X POST -H "Content-Type: application/json" \
         --data @"$file" \
         "$CONNECT_URL/connectors" | jq
  fi
}

# Déployer tous les connecteurs
for json_file in "${CONNECTORS_JSON[@]}"; do
  if [ -f "$json_file" ]; then
    deploy_connector "$json_file"
  else
    echo "⚠️  Fichier $json_file introuvable, skipping."
  fi
done

echo "✅ Tous les connecteurs ont été déployés."

# Optionnel : afficher le statut des connecteurs
echo "Statut des connecteurs:"
curl -s "$CONNECT_URL/connectors" | jq -r '.[]' | while read c; do
  curl -s "$CONNECT_URL/connectors/$c/status" | jq
done
