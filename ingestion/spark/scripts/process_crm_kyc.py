"""
Script Spark pour le traitement des données CRM et KYC
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from typing import List, Dict
import logging

def create_spark_session() -> SparkSession:
    """
    Crée et configure une session Spark
    """
    return SparkSession.builder \
        .appName("CRM-KYC-Processing") \
        .config("spark.sql.warehouse.dir", "/warehouse") \
        .config("spark.sql.debug.maxToStringFields", 100) \
        .enableHiveSupport() \
        .getOrCreate()

def read_crm_data(spark: SparkSession, source_path: str) -> DataFrame:
    """
    Lit les données CRM depuis la source
    """
    schema = StructType([
        StructField("customer_id", StringType(), False),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("address", StringType(), True),
        StructField("updated_at", TimestampType(), True)
    ])

    return spark.read \
        .format("csv") \
        .option("header", "true") \
        .schema(schema) \
        .load(source_path)

def read_kyc_data(spark: SparkSession, source_path: str) -> DataFrame:
    """
    Lit les données KYC depuis la source
    """
    schema = StructType([
        StructField("customer_id", StringType(), False),
        StructField("id_type", StringType(), True),
        StructField("id_number", StringType(), True),
        StructField("verification_status", StringType(), True),
        StructField("risk_level", StringType(), True),
        StructField("verified_at", TimestampType(), True)
    ])

    return spark.read \
        .format("csv") \
        .option("header", "true") \
        .schema(schema) \
        .load(source_path)

def join_and_transform_data(crm_df: DataFrame, kyc_df: DataFrame) -> DataFrame:
    """
    Joint et transforme les données CRM et KYC
    """
    return crm_df.join(
        kyc_df,
        "customer_id",
        "inner"
    ).select(
        col("customer_id"),
        col("first_name"),
        col("last_name"),
        col("email"),
        col("phone"),
        col("id_type"),
        col("id_number"),
        col("verification_status"),
        col("risk_level"),
        col("verified_at"),
        col("updated_at")
    )

def write_to_warehouse(df: DataFrame, target_path: str) -> None:
    """
    Écrit les données transformées dans l'entrepôt
    """
    df.write \
        .format("parquet") \
        .mode("overwrite") \
        .partitionBy("risk_level") \
        .save(target_path)

def main():
    """
    Fonction principale du traitement Spark
    """
    try:
        # Créer la session Spark
        spark = create_spark_session()
        logging.info("Session Spark créée avec succès")

        # Définir les chemins
        crm_source = "/data/raw/crm/"
        kyc_source = "/data/raw/kyc/"
        target_path = "/data/warehouse/integrated/"

        # Lire les données
        crm_df = read_crm_data(spark, crm_source)
        kyc_df = read_kyc_data(spark, kyc_source)
        logging.info(f"Données lues - CRM: {crm_df.count()} lignes, KYC: {kyc_df.count()} lignes")

        # Transformer les données
        result_df = join_and_transform_data(crm_df, kyc_df)
        logging.info(f"Données transformées - Résultat: {result_df.count()} lignes")

        # Écrire les résultats
        write_to_warehouse(result_df, target_path)
        logging.info("Données écrites avec succès dans l'entrepôt")

    except Exception as e:
        logging.error(f"Erreur lors du traitement Spark: {str(e)}")
        raise
    finally:
        if spark:
            spark.stop()
            logging.info("Session Spark arrêtée")

if __name__ == "__main__":
    main()