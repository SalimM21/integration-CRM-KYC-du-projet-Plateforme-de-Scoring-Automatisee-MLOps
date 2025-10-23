# %% [markdown]
# # Streaming Kafka → Delta Lake
# Notebook PySpark pour ingestion en streaming depuis Kafka et écriture en Delta

# %%
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType

# %%
# Créer la session Spark
spark = SparkSession.builder \
    .appName("FileRouge_Kafka_to_Delta") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoints") \
    .getOrCreate()

# %%
# Définir les schémas Avro / JSON
crm_schema = StructType([
    StructField("id", StringType(), True),
    StructField("name", StringType(), True),
    StructField("email", StringType(), True),
    StructField("created_at", TimestampType(), True)
])

transactions_schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("timestamp", TimestampType(), True)
])

# %%
# Lire les topics Kafka en streaming
crm_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-cluster-kafka-bootstrap:9092") \
    .option("subscribe", "crm_customers") \
    .option("startingOffsets", "earliest") \
    .load()

transactions_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-cluster-kafka-bootstrap:9092") \
    .option("subscribe", "transactions") \
    .option("startingOffsets", "earliest") \
    .load()

# %%
# Convertir la valeur de Kafka de bytes → string → JSON
crm_parsed = crm_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), crm_schema).alias("data")) \
    .select("data.*") \
    .withColumn("ingestion_time", current_timestamp())

transactions_parsed = transactions_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), transactions_schema).alias("data")) \
    .select("data.*") \
    .withColumn("ingestion_time", current_timestamp())

# %%
# Ecriture en Delta Lake
crm_query = crm_parsed.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/delta_crm_checkpoint") \
    .start("/delta/crm_customers")

transactions_query = transactions_parsed.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/delta_transactions_checkpoint") \
    .start("/delta/transactions")

# %%
# Afficher le flux en console (optionnel pour dev/debug)
crm_console = crm_parsed.writeStream \
    .format("console") \
    .outputMode("append") \
    .start()

transactions_console = transactions_parsed.writeStream \
    .format("console") \
    .outputMode("append") \
    .start()

# %%
# Attendre la fin (streaming continue jusqu'à stop)
crm_query.awaitTermination()
transactions_query.awaitTermination()
