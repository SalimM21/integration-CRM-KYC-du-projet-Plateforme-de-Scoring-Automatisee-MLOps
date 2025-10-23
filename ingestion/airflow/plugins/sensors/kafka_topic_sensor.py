# Sensor Kafka topic
#!/usr/bin/env python3
"""
Kafka Topic Sensor Operator
---------------------------
Permet à un DAG Airflow d’attendre qu’un topic Kafka soit créé
avant de continuer l’exécution du pipeline.
"""

import logging
import time
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from kafka.admin import KafkaAdminClient
from kafka.errors import KafkaError

logger = logging.getLogger("KafkaTopicSensor")

class KafkaTopicSensor(BaseSensorOperator):
    """
    🔍 Senseur Kafka : attend qu’un topic donné existe sur le cluster.
    """

    @apply_defaults
    def __init__(
        self,
        kafka_bootstrap_servers: str,
        topic_name: str,
        timeout: int = 300,
        poke_interval: int = 10,
        **kwargs,
    ):
        """
        :param kafka_bootstrap_servers: Liste des brokers Kafka ("broker:9092,broker2:9092")
        :param topic_name: Nom du topic à vérifier
        :param timeout: Délai max d’attente (en secondes)
        :param poke_interval: Intervalle entre deux vérifications
        """
        super().__init__(**kwargs)
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic_name = topic_name
        self.timeout = timeout
        self.poke_interval = poke_interval

    def poke(self, context):
        """
        Vérifie si le topic existe.
        """
        start_time = time.time()
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=self.kafka_bootstrap_servers)
            topics = admin_client.list_topics()
            logger.info(f"🎯 Vérification du topic Kafka '{self.topic_name}'...")
            if self.topic_name in topics:
                logger.info(f"✅ Topic '{self.topic_name}' trouvé sur le cluster Kafka.")
                return True

            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                logger.error(f"❌ Timeout : le topic '{self.topic_name}' n’existe pas après {self.timeout}s.")
                return False

            logger.info(f"⏳ Topic '{self.topic_name}' non trouvé. Nouvelle vérification dans {self.poke_interval}s...")
            time.sleep(self.poke_interval)
            return False

        except KafkaError as e:
            logger.error(f"⚠️ Erreur Kafka : {e}")
            time.sleep(self.poke_interval)
            return False
        finally:
            try:
                admin_client.close()
            except Exception:
                pass

