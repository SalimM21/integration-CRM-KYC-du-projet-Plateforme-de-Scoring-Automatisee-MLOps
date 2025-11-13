#!/bin/bash

# Script de test end-to-end du pipeline de données
# Utilisation: ./test-end-to-end.sh

set -e

echo "🧪 TEST END-TO-END - Pipeline de données complet"
echo "==============================================="

# 1. Vérifier l'état des services
echo "1️⃣ Vérification des services..."
kubectl get pods --all-namespaces | grep -E "(kafka|storage|default)" | grep Running

# 2. Injecter les données de test
echo "2️⃣ Injection des données de test..."
./inject-test-data.sh

# 3. Vérifier l'ingestion Kafka (Debezium)
echo "3️⃣ Test Debezium - Ingestion CRM..."
sleep 10
kubectl exec -n kafka my-cluster-kafka-0 -- kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic crm-customers \
  --max-messages 5 \
  --from-beginning

# 4. Vérifier les connecteurs Kafka Connect
echo "4️⃣ Vérification des connecteurs Kafka Connect..."
kubectl get kafkaconnector -n kafka

# 5. Tester l'API Scoring
echo "5️⃣ Test API Scoring..."
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d @scoring_requests.json

# 6. Vérifier les métriques Prometheus
echo "6️⃣ Vérification des métriques..."
curl http://localhost:9090/api/v1/query?query=scoring_requests_total

echo "✅ Tests end-to-end terminés!"
