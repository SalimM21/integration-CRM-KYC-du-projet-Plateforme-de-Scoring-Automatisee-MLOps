# Test de flux Kafka -> Delta
#!/usr/bin/env python3
"""
Test d’ingestion Kafka -> Delta
Script pour vérifier le flux streaming avant production
"""

import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

def main():
    # -----------------------------
    # Spark Session
    # -----------------------------
    spark = SparkSession.builder \
        .appName("Test_Streaming_Ingestion") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()

    # -----------------------------
    # Schéma JSON
    # -----------------------------
    transactions_schema = StructType([
        StructField("transaction_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("currency", StringType(), True),
        StructField("timestamp", TimestampType(), True)
    ])

    # -----------------------------
    # Lecture Kafka Topic
    # -----------------------------
    kafka_df = spark.readStream.format("kafka") \
        .option("kafka.bootstrap.servers", "kafka-cluster-kafka-bootstrap:9092") \
        .option("subscribe", "transactions") \
        .option("startingOffsets", "earliest") \
        .load()

    # -----------------------------
    # Parsing JSON
    # -----------------------------
    parsed_df = kafka_df.selectExpr("CAST(value AS STRING) as json_str") \
        .select(from_json(col("json_str"), transactions_schema).alias("data")) \
        .select("data.*")

    # -----------------------------
    # Ecriture temporaire Delta pour test
    # -----------------------------
    query = parsed_df.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "/tmp/test_streaming_checkpoint") \
        .start("/delta/test_transactions")

    # -----------------------------
    # Affichage console pour debug
    # -----------------------------
    console_query = parsed_df.writeStream \
        .format("console") \
        .outputMode("append") \
        .start()

    print("✅ Test streaming en cours... Appuyez sur Ctrl+C pour arrêter")

    # -----------------------------
    # Attente de fin (interruption manuelle)
    # -----------------------------
    try:
        query.awaitTermination()
        console_query.awaitTermination()
    except KeyboardInterrupt:
        print("⏹️ Test arrêté par l'utilisateur")
        query.stop()
        console_query.stop()

if __name__ == "__main__":
    main()
