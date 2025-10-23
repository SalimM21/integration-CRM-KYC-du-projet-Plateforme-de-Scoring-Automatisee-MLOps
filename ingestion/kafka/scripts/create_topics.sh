#!/bin/bash
# ==========================================
# Script d’automatisation création topics Kafka
# ==========================================

# Définir le bootstrap server Kafka
KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-kafka-cluster-kafka-bootstrap:9092}"

# Chemin vers les utilitaires Kafka
KAFKA_BIN="/opt/kafka/bin"

# Topics configuration
declare -A topics

topics=(
  ["crm_customers"]="3:1:604800000:delete"
  ["crm_customers_dw"]="3:1:2592000000:compact"
  ["dlq.crm_customers"]="1:1:604800000:delete"
  ["dlq.crm_customers_s3"]="1:1:604800000:delete"
  ["kyc_responses"]="2:1:259200000:delete"
  ["dlq.kyc_responses"]="1:1:604800000:delete"
  ["transactions"]="5:1:1209600000:delete"
  ["dlq.transactions"]="1:1:604800000:delete"
)

echo "Création des topics Kafka..."

for topic in "${!topics[@]}"; do
  IFS=":" read -r partitions replication retention cleanup <<< "${topics[$topic]}"
  
  echo "Création du topic: $topic"
  
  $KAFKA_BIN/kafka-topics.sh \
    --create \
    --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
    --replication-factor "$replication" \
    --partitions "$partitions" \
    --topic "$topic" \
    --config retention.ms="$retention" \
    --config cleanup.policy="$cleanup" \
    2>/dev/null || echo "Topic $topic existe déjà ou erreur."
done

echo "Tous les topics ont été créés ou étaient déjà existants."
