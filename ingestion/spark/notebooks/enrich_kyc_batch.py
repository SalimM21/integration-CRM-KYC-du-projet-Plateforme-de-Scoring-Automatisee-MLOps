# %% [markdown]
# # Enrichissement KYC (Batch)
# Notebook PySpark pour intégrer les réponses KYC via API et stocker dans Delta

# %%
import requests
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, current_timestamp
from pyspark.sql.types import StringType, StructType, StructField, TimestampType

# %%
# Spark session
spark = SparkSession.builder \
    .appName("Enrich_KYC_Batch") \
    .getOrCreate()

# %%
# Charger les données clients depuis Delta Lake
crm_df = spark.read.format("delta").load("/delta/crm_customers")

# %%
# Définir la fonction d'appel API KYC
KYC_API_URL = "https://api.kyc.example.com/check"

def call_kyc_api(customer_id):
    try:
        response = requests.get(f"{KYC_API_URL}?customer_id={customer_id}", timeout=5)
        if response.status_code == 200:
            return json.dumps(response.json())
        else:
            return None
    except Exception as e:
        return None

# UDF pour Spark
call_kyc_udf = udf(call_kyc_api, StringType())

# %%
# Appliquer l'enrichissement
crm_enriched_df = crm_df.withColumn("kyc_response_json", call_kyc_udf(col("id"))) \
                        .withColumn("enrichment_time", current_timestamp())

# %%
# Filtrer les réponses valides
crm_enriched_valid = crm_enriched_df.filter(col("kyc_response_json").isNotNull())

# %%
# Stocker les réponses JSON dans Delta / MinIO
crm_enriched_valid.write.format("delta") \
    .mode("append") \
    .option("path", "/delta/kyc_responses") \
    .save()

# %%
# Affichage pour debug
crm_enriched_valid.show(truncate=False)
