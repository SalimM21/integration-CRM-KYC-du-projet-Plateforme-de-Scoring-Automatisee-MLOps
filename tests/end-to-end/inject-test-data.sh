#!/bin/bash

# Script pour injecter les données de test dans PostgreSQL
# Utilisation: ./inject-test-data.sh

echo "🔄 Injection des données de test dans PostgreSQL..."

# Attendre que PostgreSQL soit prêt
echo "Attente de PostgreSQL..."
kubectl wait --for=condition=ready pod -l app=postgresql -n storage --timeout=300s

# Injecter les données CRM
echo "📊 Injection des données CRM..."
kubectl exec -n storage deployment/postgresql -- psql -U postgres -d scoring_db -f /tmp/crm_customers.sql

# Injecter les données de transactions
echo "💳 Injection des données de transactions..."
kubectl exec -n storage deployment/postgresql -- psql -U postgres -d scoring_db -f /tmp/transactions.sql

echo "✅ Données de test injectées avec succès!"
