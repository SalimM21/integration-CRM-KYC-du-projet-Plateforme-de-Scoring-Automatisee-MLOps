# Operator Spark Submit
#!/usr/bin/env python3
"""
Module Spark Submit Operator
Permet de soumettre des jobs Spark (batch ou streaming) depuis Python
"""

import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SparkSubmitOperator")

# -----------------------------
# Configuration globale
# -----------------------------
SPARK_HOME = "/opt/spark"
SPARK_MASTER = "local[*]"  # ou spark://<master>:7077 pour cluster

# -----------------------------
# Fonction pour soumettre un job Spark
# -----------------------------
def submit_spark_job(script_path, app_name="SparkJob", conf=None, jars=None, packages=None, args=None):
    """
    soumettre un job Spark
    :param script_path: chemin du script PySpark (.py)
    :param app_name: nom de l'application Spark
    :param conf: dict de configurations spark-submit (ex: {"spark.executor.memory": "2g"})
    :param jars: liste de jars à inclure
    :param packages: liste de packages Maven/DBJars (ex: ["org.apache.spark:spark-avro_2.12:3.4.0"])
    :param args: liste d'arguments à passer au script
    """
    if not Path(script_path).exists():
        logger.error(f"❌ Script introuvable : {script_path}")
        return False

    cmd = [f"{SPARK_HOME}/bin/spark-submit", "--master", SPARK_MASTER, "--name", app_name]

    # Ajouter conf
    if conf:
        for k, v in conf.items():
            cmd.extend(["--conf", f"{k}={v}"])

    # Ajouter jars
    if jars:
        cmd.extend(["--jars", ",".join(jars)])

    # Ajouter packages
    if packages:
        cmd.extend(["--packages", ",".join(packages)])

    # Ajouter le script
    cmd.append(script_path)

    # Ajouter arguments
    if args:
        cmd.extend(args)

    logger.info(f"🚀 Lancement Spark job : {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        logger.info(f"✅ Job Spark terminé avec succès : {app_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erreur job Spark {app_name} : {e}")
        return False

# -----------------------------
# Exemple d'utilisation
# -----------------------------
if __name__ == "__main__":
    submit_spark_job(
        script_path="/opt/spark/jobs/kafka_streaming_job.py",
        app_name="TestKafkaToDelta",
        conf={"spark.sql.shuffle.partitions": "2"},
        packages=["io.delta:delta-core_2.12:2.4.0"],
        args=["--input-topic", "transactions", "--output-path", "/delta/test_transactions"]
    )
