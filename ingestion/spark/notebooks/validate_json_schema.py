# %% [markdown]
# # Validation JSON Schema
# Notebook pour valider les messages JSON contre un schéma défini (ex: KYC)

# %%
import json
from jsonschema import validate, ValidationError
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col

# %%
# Spark session pour lecture streaming ou batch
spark = SparkSession.builder \
    .appName("Validate_JSON_Schema") \
    .getOrCreate()

# %%
# Charger le schéma JSON
with open("kyc_response_schema.json", "r") as f:
    kyc_schema = json.load(f)

# %%
# Exemple de message JSON (simulé pour test)
messages = [
    {
        "customer_id": "123",
        "kyc_status": "approved",
        "document_type": "passport",
        "issued_at": "2025-10-23T10:00:00Z"
    },
    {
        "customer_id": "456",
        "kyc_status": "pending",
        "document_type": "id_card"
        # "issued_at" manquant pour déclencher l'erreur
    }
]

# %%
# Fonction de validation
def validate_message(msg, schema):
    try:
        validate(instance=msg, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)

# %%
# Validation de chaque message
for msg in messages:
    valid, error = validate_message(msg, kyc_schema)
    if valid:
        print(f"✅ Message valide: {msg['customer_id']}")
    else:
        print(f"❌ Message invalide: {msg['customer_id']}, erreur: {error}")

# %%
# Optionnel : lire un flux Kafka en streaming et valider
kyc_stream_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-cluster-kafka-bootstrap:9092") \
    .option("subscribe", "kyc_responses") \
    .option("startingOffsets", "earliest") \
    .load()

kyc_parsed = kyc_stream_df.selectExpr("CAST(value AS STRING) as json_str")

# Convertir JSON string en colonnes Spark pour validation
# Attention : Spark ne supporte pas directement jsonschema, donc on peut écrire un UDF pour valider
from pyspark.sql.functions import udf
from pyspark.sql.types import BooleanType, StringType

def udf_validate_json(msg_str):
    try:
        msg_json = json.loads(msg_str)
        validate(instance=msg_json, schema=kyc_schema)
        return True
    except ValidationError:
        return False
    except json.JSONDecodeError:
        return False

validate_udf = udf(udf_validate_json, BooleanType())

kyc_validated = kyc_parsed.withColumn("is_valid", validate_udf(col("json_str")))

# Écriture en console pour debug
query = kyc_validated.writeStream.format("console").outputMode("append").start()
query.awaitTermination()
