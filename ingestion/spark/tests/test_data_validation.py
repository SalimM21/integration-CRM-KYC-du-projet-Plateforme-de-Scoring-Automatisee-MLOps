# Validation JSON schema
#!/usr/bin/env python3
"""
Validation JSON Schema
Vérifie que les messages respectent le schéma défini pour CRM, transactions ou KYC
"""

import json
import jsonschema
from jsonschema import validate
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import BooleanType

# -----------------------------
# Spark session
# -----------------------------
spark = SparkSession.builder \
    .appName("Test_Data_Validation") \
    .getOrCreate()

# -----------------------------
# Charger le schéma JSON
# -----------------------------
with open("kyc_response_schema.json", "r") as f:
    kyc_schema = json.load(f)

# -----------------------------
# Fonction de validation
# -----------------------------
def validate_json(record_json):
    try:
        validate(instance=json.loads(record_json), schema=kyc_schema)
        return True
    except jsonschema.exceptions.ValidationError:
        return False
    except Exception:
        return False

validate_udf = udf(validate_json, BooleanType())

# -----------------------------
# Lecture messages depuis Delta / Kafka
# -----------------------------
# Exemple Delta
df = spark.read.format("delta").load("/delta/kyc_responses")

# Si Kafka:
# df = spark.read.format("kafka") \
#     .option("kafka.bootstrap.servers", "kafka-cluster-kafka-bootstrap:9092") \
#     .option("subscribe", "kyc_responses") \
#     .load() \
#     .selectExpr("CAST(value AS STRING) as json_str")

# -----------------------------
# Validation JSON
# -----------------------------
df_validated = df.withColumn("is_valid", validate_udf(col("kyc_response_json")))

# -----------------------------
# Résultat
# -----------------------------
valid_count = df_validated.filter(col("is_valid") == True).count()
invalid_count = df_validated.filter(col("is_valid") == False).count()

print(f"✅ Messages valides : {valid_count}")
print(f"❌ Messages invalides : {invalid_count}")

# -----------------------------
# Optionnel : stocker les invalides dans DLQ
# -----------------------------
invalid_df = df_validated.filter(col("is_valid") == False)
invalid_df.write.format("delta").mode("append").save("/delta/kyc_responses_dlq")
print("📥 Messages invalides envoyés vers DLQ")
