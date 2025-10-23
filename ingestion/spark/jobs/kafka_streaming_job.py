# Version exécutable du notebook
#!/usr/bin/env python3
"""
Kafka Streaming → Delta Lake
Job PySpark pour ingérer des topics Kafka et écrire en Delta
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType

def main():
    # -----------------------------
    # Spark Session
    # -----------------------------
    spark = SparkSession.builder \
        .appName("FileRouge_Kafka_to_Delta") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

    # -----------------------------
    # Schémas JSON/Avro
    # -----------------------------
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

    # -----------------------------
    # Lecture Kafka Topics
    # -----------------------------
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

    # -----------------------------
    # Parsing Kafka messages
    # -----------------------------
    crm_parsed = crm_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), crm_schema).alias("data")) \
        .select("data.*") \
        .withColumn("ingestion_time", current_timestamp())

    transactions_parsed = transactions_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), transactions_schema).alias("data")) \
        .select("data.*") \
        .withColumn("ingestion_time", current_timestamp())

    # -----------------------------
    # Ecriture en Delta
    # -----------------------------
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

    # -----------------------------
    # Affichage console (optionnel)
    # -----------------------------
    crm_console = crm_parsed.writeStream \
        .format("console") \
        .outputMode("append") \
        .start()

    transactions_console = transactions_parsed.writeStream \
        .format("console") \
        .outputMode("append") \
        .start()

    # -----------------------------
    # Attente fin du streaming
    # -----------------------------
    crm_query.awaitTermination()
    transactions_query.awaitTermination()

if __name__ == "__main__":
    main()
