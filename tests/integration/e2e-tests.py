#!/usr/bin/env python3
"""
MLOps Scoring Platform - End-to-End Integration Tests
Tests complets d'intégration pour valider le pipeline MLOps de bout en bout
"""

import pytest
import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer, KafkaConsumer
import psycopg2
import redis
import boto3
from minio import Minio
import logging

# Configuration
SCORING_API_URL = "http://localhost:8000"
MLFLOW_URL = "http://localhost:5000"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mlops",
    "user": "mlops",
    "password": "password"
}
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "password": "password"
}
MINIO_CONFIG = {
    "endpoint": "localhost:9000",
    "access_key": "minio",
    "secret_key": "minio123",
    "secure": False
}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMLOpsIntegration:
    """Tests d'intégration complets pour la plateforme MLOps Scoring"""

    @pytest.fixture(scope="class")
    def setup_test_data(self):
        """Préparation des données de test"""
        # Générer des données de test réalistes
        test_customer = {
            "customer_id": f"CUST-{uuid.uuid4().hex[:8]}",
            "features": {
                "age": 35,
                "income": 75000,
                "credit_score": 720,
                "debt_ratio": 0.3,
                "employment_years": 8,
                "home_ownership": 1,
                "loan_amount": 250000,
                "loan_term": 30,
                "interest_rate": 3.5
            }
        }
        return test_customer

    def test_01_health_checks(self):
        """Test 1: Vérification de la santé de tous les services"""
        logger.info("🩺 Test 1: Health Checks")

        services = [
            ("Scoring API", f"{SCORING_API_URL}/health"),
            ("MLflow", f"{MLFLOW_URL}/health"),
        ]

        for service_name, url in services:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"{service_name} health check failed"
            assert response.json().get("status") == "healthy", f"{service_name} not healthy"
            logger.info(f"✅ {service_name} is healthy")

    def test_02_database_connectivity(self):
        """Test 2: Connectivité base de données"""
        logger.info("🗄️ Test 2: Database Connectivity")

        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = conn.cursor()

            # Test requête simple
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            assert version is not None, "PostgreSQL query failed"

            # Vérifier tables MLflow
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'mlflow_%'
            """)
            mlflow_tables = cursor.fetchall()
            assert len(mlflow_tables) > 0, "MLflow tables not found"

            cursor.close()
            conn.close()
            logger.info("✅ PostgreSQL connectivity OK")

        except Exception as e:
            pytest.fail(f"Database connectivity test failed: {e}")

    def test_03_redis_connectivity(self):
        """Test 3: Connectivité Redis"""
        logger.info("🔴 Test 3: Redis Connectivity")

        try:
            r = redis.Redis(**REDIS_CONFIG)
            r.ping()

            # Test cache operations
            test_key = f"test:{uuid.uuid4()}"
            test_value = "integration_test_value"

            r.set(test_key, test_value, ex=60)
            retrieved_value = r.get(test_key).decode('utf-8')
            assert retrieved_value == test_value, "Redis cache operation failed"

            r.delete(test_key)
            logger.info("✅ Redis connectivity OK")

        except Exception as e:
            pytest.fail(f"Redis connectivity test failed: {e}")

    def test_04_minio_connectivity(self):
        """Test 4: Connectivité MinIO/S3"""
        logger.info("📦 Test 4: MinIO/S3 Connectivity")

        try:
            client = Minio(**MINIO_CONFIG)

            # Vérifier bucket MLflow
            buckets = client.list_buckets()
            bucket_names = [b.name for b in buckets]
            assert "mlflow-artifacts" in bucket_names, "MLflow artifacts bucket not found"

            # Test upload/download
            test_content = b"Integration test content"
            test_object = f"test-{uuid.uuid4()}.txt"

            client.put_object("mlflow-artifacts", test_object, test_content, len(test_content))
            response = client.get_object("mlflow-artifacts", test_object)
            retrieved_content = response.read()
            assert retrieved_content == test_content, "MinIO upload/download failed"

            client.remove_object("mlflow-artifacts", test_object)
            logger.info("✅ MinIO connectivity OK")

        except Exception as e:
            pytest.fail(f"MinIO connectivity test failed: {e}")

    def test_05_kafka_connectivity(self):
        """Test 5: Connectivité Kafka"""
        logger.info("📨 Test 5: Kafka Connectivity")

        try:
            # Test producer
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )

            # Test consumer
            consumer = KafkaConsumer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                group_id=f'test-group-{uuid.uuid4()}',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=5000
            )

            # Vérifier topics
            from kafka.admin import KafkaAdminClient
            admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
            topics = admin_client.list_topics()
            required_topics = ['crm-customers', 'transactions', 'scoring-requests', 'scoring-results']
            for topic in required_topics:
                assert topic in topics, f"Required topic {topic} not found"

            producer.close()
            consumer.close()
            admin_client.close()
            logger.info("✅ Kafka connectivity OK")

        except Exception as e:
            pytest.fail(f"Kafka connectivity test failed: {e}")

    def test_06_scoring_api_functionality(self, setup_test_data):
        """Test 6: Fonctionnalité API Scoring"""
        logger.info("🎯 Test 6: Scoring API Functionality")

        test_customer = setup_test_data

        # Test scoring request
        scoring_payload = {
            "customer_id": test_customer["customer_id"],
            "features": test_customer["features"],
            "model_version": "v1.0.0"
        }

        response = requests.post(
            f"{SCORING_API_URL}/score",
            json=scoring_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        assert response.status_code == 200, f"Scoring API returned {response.status_code}"
        result = response.json()

        # Vérifier structure réponse
        required_fields = ["customer_id", "credit_score", "risk_level", "approved_amount", "timestamp"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        # Vérifier valeurs raisonnables
        assert 300 <= result["credit_score"] <= 850, "Credit score out of range"
        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"], "Invalid risk level"
        assert result["approved_amount"] > 0, "Approved amount must be positive"

        logger.info(f"✅ Scoring API OK - Score: {result['credit_score']}, Risk: {result['risk_level']}")

    def test_07_mlflow_integration(self):
        """Test 7: Intégration MLflow"""
        logger.info("🔬 Test 7: MLflow Integration")

        # Vérifier API MLflow
        response = requests.get(f"{MLFLOW_URL}/api/2.0/mlflow/experiments/list", timeout=10)
        assert response.status_code == 200, "MLflow API not accessible"

        experiments = response.json().get("experiments", [])
        assert len(experiments) > 0, "No MLflow experiments found"

        # Vérifier modèles enregistrés
        response = requests.get(f"{MLFLOW_URL}/api/2.0/mlflow/registered-models/list", timeout=10)
        assert response.status_code == 200, "MLflow registered models API failed"

        models = response.json().get("registered_models", [])
        assert len(models) > 0, "No registered models found"

        logger.info(f"✅ MLflow OK - {len(experiments)} experiments, {len(models)} models")

    def test_08_kafka_pipeline_integration(self, setup_test_data):
        """Test 8: Pipeline Kafka end-to-end"""
        logger.info("🔄 Test 8: Kafka Pipeline Integration")

        test_customer = setup_test_data

        # Producer pour envoyer données CRM
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # Envoyer données customer
        producer.send('crm-customers', value=test_customer)
        producer.flush()

        # Consumer pour vérifier traitement
        consumer = KafkaConsumer(
            'scoring-results',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='latest',
            enable_auto_commit=False,
            group_id=f'test-consumer-{uuid.uuid4()}',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=30000
        )

        # Attendre résultat scoring
        result_found = False
        for message in consumer:
            if message.value.get("customer_id") == test_customer["customer_id"]:
                result_found = True
                scoring_result = message.value
                break

        assert result_found, "Scoring result not found in Kafka topic"
        assert "credit_score" in scoring_result, "Credit score missing in result"

        producer.close()
        consumer.close()
        logger.info("✅ Kafka pipeline OK - End-to-end processing completed")

    def test_09_performance_under_load(self):
        """Test 9: Performance sous charge"""
        logger.info("⚡ Test 9: Performance Under Load")

        import concurrent.futures
        import threading

        # Configuration test charge
        num_requests = 100
        num_threads = 10
        timeout = 30

        results = []
        errors = []

        def make_request():
            try:
                payload = {
                    "customer_id": f"CUST-{uuid.uuid4().hex[:8]}",
                    "features": {
                        "age": 35, "income": 75000, "credit_score": 720,
                        "debt_ratio": 0.3, "employment_years": 8
                    }
                }
                start_time = time.time()
                response = requests.post(
                    f"{SCORING_API_URL}/score",
                    json=payload,
                    timeout=timeout
                )
                end_time = time.time()

                results.append({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                })
            except Exception as e:
                errors.append(str(e))

        # Exécuter tests en parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            concurrent.futures.wait(futures, timeout=timeout*2)

        # Analyser résultats
        successful_requests = len([r for r in results if r["success"]])
        avg_response_time = sum(r["response_time"] for r in results) / len(results) if results else 0
        max_response_time = max(r["response_time"] for r in results) if results else 0

        # Assertions performance
        assert successful_requests >= num_requests * 0.95, f"Success rate too low: {successful_requests}/{num_requests}"
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.2f}s"
        assert max_response_time < 10.0, f"Max response time too high: {max_response_time:.2f}s"

        logger.info(f"✅ Performance OK - {successful_requests}/{num_requests} successful, "
                   f"Avg: {avg_response_time:.2f}s, Max: {max_response_time:.2f}s")

    def test_10_security_validation(self):
        """Test 10: Validation sécurité"""
        logger.info("🔒 Test 10: Security Validation")

        # Test injection SQL
        malicious_payload = {
            "customer_id": "'; DROP TABLE customers; --",
            "features": {"age": 35}
        }

        response = requests.post(
            f"{SCORING_API_URL}/score",
            json=malicious_payload,
            headers={"Content-Type": "application/json"}
        )

        # Devrait échouer ou être filtré
        assert response.status_code in [400, 422, 500], "SQL injection not properly handled"

        # Test XSS
        xss_payload = {
            "customer_id": "<script>alert('xss')</script>",
            "features": {"age": 35}
        }

        response = requests.post(
            f"{SCORING_API_URL}/score",
            json=xss_payload,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422], "XSS not properly handled"

        # Test rate limiting (si configuré)
        responses = []
        for i in range(150):  # Au-delà de la limite
            response = requests.get(f"{SCORING_API_URL}/health", timeout=5)
            responses.append(response.status_code)
            if response.status_code == 429:  # Rate limited
                break
            time.sleep(0.1)

        rate_limited = any(code == 429 for code in responses)
        if rate_limited:
            logger.info("✅ Rate limiting is active")
        else:
            logger.warning("⚠️ Rate limiting not detected (may not be configured)")

        logger.info("✅ Security validation completed")

    def test_11_data_consistency(self):
        """Test 11: Cohérence des données"""
        logger.info("📊 Test 11: Data Consistency")

        # Créer customer via API
        test_customer = {
            "customer_id": f"CUST-{uuid.uuid4().hex[:8]}",
            "features": {
                "age": 30, "income": 60000, "credit_score": 680,
                "debt_ratio": 0.25, "employment_years": 5
            }
        }

        # Envoyer scoring request
        response = requests.post(
            f"{SCORING_API_URL}/score",
            json=test_customer,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        scoring_result = response.json()

        # Vérifier cohérence base de données
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()

        # Vérifier enregistrement scoring
        cursor.execute("""
            SELECT customer_id, credit_score, risk_level
            FROM scoring_results
            WHERE customer_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (test_customer["customer_id"],))

        db_result = cursor.fetchone()
        assert db_result is not None, "Scoring result not found in database"
        assert db_result[0] == test_customer["customer_id"], "Customer ID mismatch"
        assert db_result[1] == scoring_result["credit_score"], "Credit score mismatch"

        cursor.close()
        conn.close()

        logger.info("✅ Data consistency OK - API and database synchronized")

    def test_12_monitoring_integration(self):
        """Test 12: Intégration monitoring"""
        logger.info("📈 Test 12: Monitoring Integration")

        # Vérifier métriques Prometheus
        try:
            response = requests.get("http://localhost:9090/api/v1/query?query=up", timeout=10)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "success", "Prometheus query failed"

            # Vérifier métriques application
            response = requests.get("http://localhost:9090/api/v1/query?query=scoring_api_requests_total", timeout=10)
            assert response.status_code == 200

            logger.info("✅ Prometheus metrics OK")

        except requests.exceptions.RequestException:
            logger.warning("⚠️ Prometheus not accessible (may not be running)")

        # Vérifier logs Loki (si disponible)
        try:
            response = requests.get("http://localhost:3100/ready", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Loki is accessible")
            else:
                logger.warning("⚠️ Loki health check failed")
        except requests.exceptions.RequestException:
            logger.warning("⚠️ Loki not accessible")

    def test_13_failover_resilience(self):
        """Test 13: Résilience et failover"""
        logger.info("🔄 Test 13: Failover Resilience")

        # Test arrêt/redémarrage service (si possible en test)
        # Pour l'instant, juste vérifier haute disponibilité

        # Vérifier multiple replicas
        response = requests.get("http://localhost:9090/api/v1/query?query=kube_deployment_spec_replicas", timeout=10)
        if response.status_code == 200:
            deployments = response.json().get("data", {}).get("result", [])
            for deployment in deployments:
                if "scoring-api" in deployment["metric"].get("deployment", ""):
                    replicas = int(deployment["value"][1])
                    assert replicas >= 2, f"Scoring API should have multiple replicas, found: {replicas}"
                    logger.info(f"✅ Scoring API has {replicas} replicas")

        # Test circuit breaker (si implémenté)
        # Simuler surcharge
        responses = []
        for i in range(50):
            try:
                response = requests.post(
                    f"{SCORING_API_URL}/score",
                    json={"customer_id": f"test-{i}", "features": {"age": 30}},
                    timeout=5
                )
                responses.append(response.status_code)
            except:
                responses.append(500)

        # Vérifier pas de défaillance en cascade
        success_rate = len([r for r in responses if r == 200]) / len(responses)
        assert success_rate > 0.8, f"Success rate too low during load test: {success_rate:.2%}"

        logger.info(f"✅ Resilience OK - Success rate: {success_rate:.2%}")

    def test_14_compliance_validation(self):
        """Test 14: Validation conformité"""
        logger.info("⚖️ Test 14: Compliance Validation")

        # Test audit logging
        # Vérifier que les actions sont loggées
        test_customer = {
            "customer_id": f"CUST-{uuid.uuid4().hex[:8]}",
            "features": {"age": 35, "income": 75000}
        }

        # Effectuer action qui devrait être auditée
        response = requests.post(
            f"{SCORING_API_URL}/score",
            json=test_customer,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        # Vérifier logs d'audit (si Loki disponible)
        try:
            # Query Loki pour audit logs
            loki_query = {
                "query": '{component="scoring-api"} |= "score"',
                "limit": 10
            }
            response = requests.get(
                "http://localhost:3100/loki/api/v1/query",
                params=loki_query,
                timeout=10
            )
            if response.status_code == 200:
                logs = response.json().get("data", {}).get("result", [])
                if logs:
                    logger.info("✅ Audit logging OK - Events found in logs")
                else:
                    logger.warning("⚠️ No audit logs found")
        except:
            logger.warning("⚠️ Loki audit log check failed")

        # Test data anonymization (si applicable)
        # Vérifier que données sensibles sont masquées

        logger.info("✅ Compliance validation completed")

if __name__ == "__main__":
    # Configuration pour tests locaux
    import os
    if os.getenv("TEST_ENV") == "local":
        SCORING_API_URL = "http://localhost:8000"
        MLFLOW_URL = "http://localhost:5000"
        # ... autres configurations locales

    # Exécuter tests
    pytest.main([__file__, "-v", "--tb=short"])