#!/usr/bin/env python3
"""
MLOps Scoring Platform - Chaos Engineering Tests
Tests de chaos pour valider la résilience et la haute disponibilité
"""

import asyncio
import aiohttp
import json
import time
import random
import subprocess
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Configuration
SCORING_API_URL = "http://localhost:8000"
CHAOS_DURATION = 120  # 2 minutes par test
RECOVERY_TIME = 60   # 1 minute pour récupération
NORMAL_LOAD_USERS = 20

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChaosExperiment:
    """Expérience de chaos engineering"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time = None
        self.end_time = None
        self.baseline_metrics = {}
        self.chaos_metrics = {}
        self.recovery_metrics = {}

    def start_experiment(self):
        """Démarrer l'expérience"""
        self.start_time = datetime.now()
        logger.info(f"🌀 Starting chaos experiment: {self.name}")
        logger.info(f"📝 Description: {self.description}")

    def end_experiment(self):
        """Terminer l'expérience"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"✅ Chaos experiment completed: {self.name} ({duration:.1f}s)")

class PodFailureChaos(ChaosExperiment):
    """Test de panne de pod"""

    def __init__(self):
        super().__init__(
            "Pod Failure",
            "Simulate pod crashes to test self-healing and high availability"
        )

    def inject_chaos(self):
        """Injecter le chaos en supprimant un pod"""
        try:
            # Identifier un pod scoring-api
            result = subprocess.run([
                "kubectl", "get", "pods", "-l", "app.kubernetes.io/component=scoring-api",
                "-o", "jsonpath={.items[0].metadata.name}"
            ], capture_output=True, text=True, check=True)

            pod_name = result.stdout.strip()
            if not pod_name:
                logger.error("No scoring-api pod found")
                return False

            logger.info(f"💥 Killing pod: {pod_name}")

            # Supprimer le pod
            subprocess.run([
                "kubectl", "delete", "pod", pod_name, "--grace-period=0", "--force"
            ], check=True)

            # Attendre redémarrage
            time.sleep(10)

            # Vérifier que le pod est redémarré
            result = subprocess.run([
                "kubectl", "get", "pods", "-l", "app.kubernetes.io/component=scoring-api",
                "-o", "jsonpath={.items[*].status.phase}"
            ], capture_output=True, text=True)

            phases = result.stdout.strip().split()
            running_pods = sum(1 for phase in phases if phase == "Running")

            logger.info(f"🔄 Pods status after chaos: {running_pods} running")
            return running_pods > 0

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to inject pod failure chaos: {e}")
            return False

class NetworkLatencyChaos(ChaosExperiment):
    """Test de latence réseau"""

    def __init__(self):
        super().__init__(
            "Network Latency",
            "Add network latency to test performance under degraded conditions"
        )

    def inject_chaos(self):
        """Injecter de la latence réseau"""
        try:
            # Utiliser tc (traffic control) pour ajouter latence
            # Note: Nécessite privilèges root et tc installé
            latency_ms = 500

            logger.info(f"🐌 Adding {latency_ms}ms network latency")

            # Cette commande nécessite des privilèges et tc installé
            # En production, utiliser un outil comme Pumba ou Chaos Mesh
            subprocess.run([
                "sudo", "tc", "qdisc", "add", "dev", "eth0", "root", "netem", "delay", f"{latency_ms}ms"
            ], check=True)

            time.sleep(CHAOS_DURATION)

            # Restaurer
            subprocess.run([
                "sudo", "tc", "qdisc", "del", "dev", "eth0", "root"
            ], check=True)

            logger.info("🔄 Network latency removed")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to inject network latency: {e}")
            return False

class ResourceExhaustionChaos(ChaosExperiment):
    """Test d'épuisement des ressources"""

    def __init__(self):
        super().__init__(
            "Resource Exhaustion",
            "Consume system resources to test limits and autoscaling"
        )

    def inject_chaos(self):
        """Épuiser les ressources CPU/mémoire"""
        try:
            # Créer un pod qui consomme beaucoup de ressources
            logger.info("🔥 Creating resource-intensive pod")

            chaos_pod = """
apiVersion: v1
kind: Pod
metadata:
  name: chaos-resource-consumer
  labels:
    app: chaos-consumer
spec:
  containers:
  - name: stress
    image: progrium/stress
    command: ["stress", "--cpu", "4", "--vm", "2", "--vm-bytes", "512M", "--timeout", "120"]
  resources:
    requests:
      cpu: "500m"
      memory: "256Mi"
    limits:
      cpu: "2000m"
      memory: "1Gi"
"""

            # Appliquer le pod chaos
            with open('/tmp/chaos-pod.yaml', 'w') as f:
                f.write(chaos_pod)

            subprocess.run([
                "kubectl", "apply", "-f", "/tmp/chaos-pod.yaml"
            ], check=True)

            # Attendre que le chaos fasse effet
            time.sleep(CHAOS_DURATION)

            # Nettoyer
            subprocess.run([
                "kubectl", "delete", "-f", "/tmp/chaos-pod.yaml"
            ], check=True)

            logger.info("🧹 Resource exhaustion chaos cleaned up")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to inject resource exhaustion: {e}")
            return False

class DatabaseFailureChaos(ChaosExperiment):
    """Test de panne base de données"""

    def __init__(self):
        super().__init__(
            "Database Failure",
            "Simulate database outages to test resilience and fallback"
        )

    def inject_chaos(self):
        """Simuler une panne de base de données"""
        try:
            # Identifier le pod PostgreSQL
            result = subprocess.run([
                "kubectl", "get", "pods", "-l", "app.kubernetes.io/name=postgresql",
                "-o", "jsonpath={.items[0].metadata.name}"
            ], capture_output=True, text=True, check=True)

            db_pod = result.stdout.strip()
            if not db_pod:
                logger.error("No PostgreSQL pod found")
                return False

            logger.info(f"💥 Simulating database failure: {db_pod}")

            # Arrêter temporairement le pod (scale to 0 puis remettre)
            # Alternative: utiliser network policies pour isoler

            # Créer une network policy pour bloquer le trafic vers la DB
            network_policy = """
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chaos-db-isolation
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: postgresql
  policyTypes: [Ingress]
  ingress: []  # Bloquer tout trafic entrant
"""

            with open('/tmp/chaos-db-policy.yaml', 'w') as f:
                f.write(network_policy)

            subprocess.run([
                "kubectl", "apply", "-f", "/tmp/chaos-db-policy.yaml"
            ], check=True)

            time.sleep(CHAOS_DURATION)

            # Restaurer
            subprocess.run([
                "kubectl", "delete", "-f", "/tmp/chaos-db-policy.yaml"
            ], check=True)

            logger.info("🔄 Database connectivity restored")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to inject database failure: {e}")
            return False

class ChaosLoadTester:
    """Testeur de charge pendant les expériences chaos"""

    def __init__(self):
        self.session = None
        self.results = {
            'baseline': {'response_times': [], 'errors': []},
            'chaos': {'response_times': [], 'errors': []},
            'recovery': {'response_times': [], 'errors': []}
        }

    async def init_session(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def generate_load(self, duration: int, phase: str):
        """Générer charge pendant une phase donnée"""
        logger.info(f"📊 Generating load during {phase} phase ({duration}s)")

        end_time = time.time() + duration

        while time.time() < end_time:
            try:
                payload = {
                    "customer_id": f"CHAOS-{random.randint(1000,9999)}",
                    "features": {
                        "age": random.randint(25, 65),
                        "income": random.randint(30000, 100000),
                        "credit_score": random.randint(500, 800)
                    }
                }

                start_time = time.time()
                async with self.session.post(
                    f"{SCORING_API_URL}/score",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        self.results[phase]['response_times'].append(response_time)
                    else:
                        error = f"HTTP {response.status}"
                        self.results[phase]['errors'].append(error)

            except Exception as e:
                self.results[phase]['errors'].append(str(e))

            # Petit délai entre requêtes
            await asyncio.sleep(0.1)

    def analyze_results(self):
        """Analyser les résultats des tests chaos"""
        print("\n" + "="*80)
        print("🎭 CHAOS ENGINEERING TEST RESULTS")
        print("="*80)

        for phase in ['baseline', 'chaos', 'recovery']:
            data = self.results[phase]
            response_times = data['response_times']
            errors = data['errors']

            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                success_rate = len(response_times) / (len(response_times) + len(errors)) * 100

                print(f"\n📊 {phase.upper()} PHASE:")
                print(f"  Requests: {len(response_times) + len(errors)}")
                print(f"  Success Rate: {success_rate:.1f}%")
                print(f"  Avg Response Time: {avg_time:.3f}s")
                print(f"  Max Response Time: {max_time:.3f}s")
                print(f"  Errors: {len(errors)}")

                if errors:
                    print("  Top Errors:")
                    error_counts = {}
                    for error in errors[:10]:
                        error_counts[error] = error_counts.get(error, 0) + 1
                    for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                        print(f"    {count}x: {error[:60]}...")
            else:
                print(f"\n❌ {phase.upper()} PHASE: No successful requests")

        # Analyse comparative
        print(f"\n🔍 CHAOS IMPACT ANALYSIS:")

        if self.results['baseline']['response_times'] and self.results['chaos']['response_times']:
            baseline_avg = sum(self.results['baseline']['response_times']) / len(self.results['baseline']['response_times'])
            chaos_avg = sum(self.results['chaos']['response_times']) / len(self.results['chaos']['response_times'])

            degradation = ((chaos_avg - baseline_avg) / baseline_avg) * 100

            if abs(degradation) < 50:
                print(f"✅ System resilience: GOOD (degradation: {degradation:+.1f}%)")
            elif abs(degradation) < 200:
                print(f"⚠️ System resilience: MODERATE (degradation: {degradation:+.1f}%)")
            else:
                print(f"❌ System resilience: POOR (degradation: {degradation:+.1f}%)")

        # Recommandations
        recommendations = []

        chaos_errors = len(self.results['chaos']['errors'])
        baseline_errors = len(self.results['baseline']['errors'])

        if chaos_errors > baseline_errors * 2:
            recommendations.append("Implement better error handling and circuit breakers")
        if degradation > 100:
            recommendations.append("Consider implementing request queuing or rate limiting")
        if len(self.results['recovery']['errors']) > len(self.results['chaos']['errors']):
            recommendations.append("Improve recovery mechanisms and health checks")

        if recommendations:
            print("💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")

        print("\n" + "="*80)

async def run_chaos_experiment(experiment: ChaosExperiment, load_tester: ChaosLoadTester):
    """Exécuter une expérience de chaos"""

    # Phase baseline
    logger.info("📈 Establishing baseline performance...")
    await load_tester.generate_load(30, 'baseline')  # 30s baseline

    # Injecter chaos
    experiment.start_experiment()
    chaos_success = experiment.inject_chaos()

    if chaos_success:
        # Phase chaos avec charge
        logger.info("🔥 Chaos active - monitoring impact...")
        await load_tester.generate_load(CHAOS_DURATION, 'chaos')

        # Phase récupération
        logger.info("🔄 Recovery phase - monitoring restoration...")
        await load_tester.generate_load(RECOVERY_TIME, 'recovery')

    experiment.end_experiment()

    return chaos_success

async def main():
    """Fonction principale des tests chaos"""
    print("🎭 MLOps Scoring Platform - Chaos Engineering Tests")
    print("="*60)

    # Initialiser le testeur de charge
    load_tester = ChaosLoadTester()
    await load_tester.init_session()

    try:
        # Liste des expériences de chaos
        experiments = [
            PodFailureChaos(),
            # NetworkLatencyChaos(),  # Désactivé - nécessite tc et sudo
            # ResourceExhaustionChaos(),  # Désactivé - nécessite stress tool
            # DatabaseFailureChaos(),  # Désactivé - nécessite network policies
        ]

        # Exécuter chaque expérience
        for experiment in experiments:
            logger.info(f"\n🚀 Preparing chaos experiment: {experiment.name}")

            try:
                success = await run_chaos_experiment(experiment, load_tester)
                if success:
                    logger.info(f"✅ {experiment.name} experiment completed successfully")
                else:
                    logger.error(f"❌ {experiment.name} experiment failed")

            except Exception as e:
                logger.error(f"💥 {experiment.name} experiment crashed: {e}")

            # Pause entre expériences
            await asyncio.sleep(30)

        # Analyser résultats globaux
        load_tester.analyze_results()

    finally:
        await load_tester.close_session()

if __name__ == "__main__":
    import os

    # Configuration depuis variables d'environnement
    SCORING_API_URL = os.getenv("SCORING_API_URL", "http://localhost:8000")
    CHAOS_DURATION = int(os.getenv("CHAOS_DURATION", "120"))
    RECOVERY_TIME = int(os.getenv("RECOVERY_TIME", "60"))
    NORMAL_LOAD_USERS = int(os.getenv("NORMAL_LOAD_USERS", "20"))

    # Exécuter tests chaos
    asyncio.run(main())