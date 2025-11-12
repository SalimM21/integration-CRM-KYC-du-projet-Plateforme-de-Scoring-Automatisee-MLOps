#!/bin/bash

# Script pour enregistrer les schémas Avro/JSON dans Apicurio Registry

# Attendre que le registry soit prêt
echo "Attente du Schema Registry..."
kubectl wait --for=condition=ready pod -l app=apicurio-registry -n kafka --timeout=300s

# Port forward pour accéder au registry
kubectl port-forward svc/apicurio-registry-service 8080:8080 -n kafka &
PORT_FORWARD_PID=$!

sleep 5

# Fonction pour enregistrer un schéma
register_schema() {
    local subject=$1
    local schema_file=$2

    echo "Enregistrement du schéma pour $subject..."

    curl -X POST http://localhost:8080/apis/registry/v2/groups/default/artifacts \
         -H "Content-Type: application/json" \
         -H "X-Registry-ArtifactId: $subject" \
         -d @"$schema_file"

    echo ""
}

# Schéma pour crm-customers
cat > crm_customer_schema.json << 'EOF'
{
  "type": "record",
  "name": "Customer",
  "namespace": "com.scoring.crm",
  "fields": [
    {
      "name": "customer_id",
      "type": "string"
    },
    {
      "name": "first_name",
      "type": "string"
    },
    {
      "name": "last_name",
      "type": "string"
    },
    {
      "name": "email",
      "type": "string"
    },
    {
      "name": "phone",
      "type": ["null", "string"],
      "default": null
    },
    {
      "name": "address",
      "type": ["null", "string"],
      "default": null
    },
    {
      "name": "registration_date",
      "type": "string"
    },
    {
      "name": "status",
      "type": {
        "type": "enum",
        "name": "CustomerStatus",
        "symbols": ["ACTIVE", "INACTIVE", "SUSPENDED"]
      }
    }
  ]
}
EOF

# Schéma pour transactions
cat > transaction_schema.json << 'EOF'
{
  "type": "record",
  "name": "Transaction",
  "namespace": "com.scoring.transaction",
  "fields": [
    {
      "name": "transaction_id",
      "type": "string"
    },
    {
      "name": "customer_id",
      "type": "string"
    },
    {
      "name": "amount",
      "type": "double"
    },
    {
      "name": "currency",
      "type": "string",
      "default": "EUR"
    },
    {
      "name": "transaction_type",
      "type": {
        "type": "enum",
        "name": "TransactionType",
        "symbols": ["DEBIT", "CREDIT", "TRANSFER"]
      }
    },
    {
      "name": "timestamp",
      "type": "long"
    },
    {
      "name": "merchant",
      "type": ["null", "string"],
      "default": null
    },
    {
      "name": "category",
      "type": ["null", "string"],
      "default": null
    }
  ]
}
EOF

# Schéma pour kyc-responses
cat > kyc_response_schema.json << 'EOF'
{
  "type": "record",
  "name": "KYCResponse",
  "namespace": "com.scoring.kyc",
  "fields": [
    {
      "name": "customer_id",
      "type": "string"
    },
    {
      "name": "kyc_status",
      "type": {
        "type": "enum",
        "name": "KYCStatus",
        "symbols": ["VERIFIED", "PENDING", "REJECTED", "IN_PROGRESS"]
      }
    },
    {
      "name": "risk_score",
      "type": "float"
    },
    {
      "name": "documents_verified",
      "type": "boolean"
    },
    {
      "name": "verification_date",
      "type": "long"
    },
    {
      "name": "comments",
      "type": ["null", "string"],
      "default": null
    }
  ]
}
EOF

# Schéma pour scoring-results
cat > scoring_result_schema.json << 'EOF'
{
  "type": "record",
  "name": "ScoringResult",
  "namespace": "com.scoring.result",
  "fields": [
    {
      "name": "customer_id",
      "type": "string"
    },
    {
      "name": "scoring_request_id",
      "type": "string"
    },
    {
      "name": "credit_score",
      "type": "int"
    },
    {
      "name": "risk_level",
      "type": {
        "type": "enum",
        "name": "RiskLevel",
        "symbols": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
      }
    },
    {
      "name": "approved_amount",
      "type": "double"
    },
    {
      "name": "interest_rate",
      "type": "float"
    },
    {
      "name": "scoring_timestamp",
      "type": "long"
    },
    {
      "name": "model_version",
      "type": "string"
    }
  ]
}
EOF

# Enregistrer les schémas
register_schema "crm-customers-value" "crm_customer_schema.json"
register_schema "transactions-value" "transaction_schema.json"
register_schema "kyc-responses-value" "kyc_response_schema.json"
register_schema "scoring-results-value" "scoring_result_schema.json"

# Nettoyer
kill $PORT_FORWARD_PID
rm -f *.json

echo "Schémas enregistrés avec succès!"