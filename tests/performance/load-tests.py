#!/usr/bin/env python3
"""
MLOps Scoring Platform - Performance & Load Tests
Tests de performance avancés avec simulation de charge réelle
"""

import asyncio
import aiohttp
import json
import time
import statistics
import uuid
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading
import psutil
import os

# Configuration
SCORING_API_URL = "http://localhost:8000"
DURATION_SECONDS = 300  # 5 minutes
CONCURRENT_USERS = 50
RAMP_UP_TIME = 30  # seconds
THINK_TIME_MIN = 1  # seconds
THINK_TIME_MAX = 3  # seconds

class LoadTestResult:
    """Résultat d'un test de charge"""
    def __init__(self):
        self.requests_total = 0
        self.requests_successful = 0
        self.requests_failed = 0
        self.response_times = []
        self.errors = []
        self.start_time = None
        self.end_time = None

    def add_result(self, response_time: float, status_code: int, error: str = None):
        self.requests_total += 1
        if status_code == 200 and not error:
            self.requests_successful += 1
            self.response_times.append(response_time)
        else:
            self.requests_failed += 1
            if error:
                self.errors.append(error)

    @property
    def success_rate(self) -> float:
        return self.requests_successful / self.requests_total if self.requests_total > 0 else 0

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def p95_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times) if self.response_times else 0

    @property
    def p99_response_time(self) -> float:
        return statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times) if self.response_times else 0

    @property
    def throughput(self) -> float:
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 1
        return self.requests_total / duration

class PerformanceMonitor:
    """Moniteur de performance système"""

    def __init__(self):
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_io = []
        self.network_io = []
        self.timestamps = []
        self.monitoring = False

    def start_monitoring(self):
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)

    def _monitor_loop(self):
        while self.monitoring:
            timestamp = datetime.now()
            self.timestamps.append(timestamp)

            # CPU usage
            self.cpu_usage.append(psutil.cpu_percent(interval=1))

            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.append(memory.percent)

            # Disk I/O (simplifié)
            try:
                disk = psutil.disk_io_counters()
                self.disk_io.append(disk.read_bytes + disk.write_bytes)
            except:
                self.disk_io.append(0)

            # Network I/O (simplifié)
            try:
                net = psutil.net_io_counters()
                self.network_io.append(net.bytes_sent + net.bytes_recv)
            except:
                self.network_io.append(0)

            time.sleep(5)  # Monitor every 5 seconds

class LoadTester:
    """Testeur de charge avancé"""

    def __init__(self):
        self.session = None
        self.results = LoadTestResult()
        self.monitor = PerformanceMonitor()

    async def init_session(self):
        """Initialiser la session HTTP"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close_session(self):
        """Fermer la session HTTP"""
        if self.session:
            await self.session.close()

    def generate_test_payload(self) -> Dict[str, Any]:
        """Générer une payload de test réaliste"""
        customer_id = f"CUST-{uuid.uuid4().hex[:8]}"

        # Distribution réaliste des données
        import random
        age = random.randint(18, 80)
        income = random.randint(20000, 200000)
        credit_score = random.randint(300, 850)
        debt_ratio = random.uniform(0.1, 0.8)
        employment_years = random.randint(0, 40)

        return {
            "customer_id": customer_id,
            "features": {
                "age": age,
                "income": income,
                "credit_score": credit_score,
                "debt_ratio": debt_ratio,
                "employment_years": employment_years,
                "home_ownership": random.choice([0, 1]),
                "loan_amount": random.randint(50000, 500000),
                "loan_term": random.choice([15, 20, 30]),
                "interest_rate": random.uniform(2.5, 8.5)
            },
            "model_version": "v1.0.0"
        }

    async def make_request(self, user_id: int) -> tuple:
        """Effectuer une requête de test"""
        if not self.session:
            await self.init_session()

        payload = self.generate_test_payload()

        start_time = time.time()
        try:
            async with self.session.post(
                f"{SCORING_API_URL}/score",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()

                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        return response_time, response.status, None, result
                    except json.JSONDecodeError as e:
                        return response_time, response.status, f"Invalid JSON: {e}", None
                else:
                    return response_time, response.status, f"HTTP {response.status}: {response_text}", None

        except Exception as e:
            response_time = time.time() - start_time
            return response_time, 0, str(e), None

    async def user_simulation(self, user_id: int, results_queue: asyncio.Queue):
        """Simulation d'un utilisateur virtuel"""
        await asyncio.sleep(random.uniform(0, RAMP_UP_TIME))  # Ramp-up

        end_time = time.time() + DURATION_SECONDS

        while time.time() < end_time:
            # Effectuer requête
            response_time, status_code, error, result = await self.make_request(user_id)

            # Ajouter résultat
            results_queue.put_nowait((response_time, status_code, error, result))

            # Think time
            think_time = random.uniform(THINK_TIME_MIN, THINK_TIME_MAX)
            await asyncio.sleep(think_time)

    async def run_load_test(self) -> LoadTestResult:
        """Exécuter le test de charge complet"""
        print(f"🚀 Starting load test: {CONCURRENT_USERS} users for {DURATION_SECONDS}s")

        self.results.start_time = datetime.now()
        self.monitor.start_monitoring()

        # Queue pour collecter résultats
        results_queue = asyncio.Queue()

        # Créer tâches utilisateurs
        tasks = []
        for user_id in range(CONCURRENT_USERS):
            task = asyncio.create_task(self.user_simulation(user_id, results_queue))
            tasks.append(task)

        # Collecter résultats en temps réel
        try:
            await asyncio.wait_for(self._collect_results(results_queue), timeout=DURATION_SECONDS + 10)
        except asyncio.TimeoutError:
            print("⚠️ Test duration exceeded, stopping collection")

        # Arrêter toutes les tâches
        for task in tasks:
            task.cancel()

        # Attendre arrêt propre
        await asyncio.gather(*tasks, return_exceptions=True)

        self.results.end_time = datetime.now()
        self.monitor.stop_monitoring()

        return self.results

    async def _collect_results(self, results_queue: asyncio.Queue):
        """Collecter les résultats des requêtes"""
        while True:
            try:
                response_time, status_code, error, result = await asyncio.wait_for(
                    results_queue.get(), timeout=1.0
                )
                self.results.add_result(response_time, status_code, error)
            except asyncio.TimeoutError:
                continue

    def generate_report(self, results: LoadTestResult):
        """Générer rapport de performance détaillé"""
        print("\n" + "="*80)
        print("📊 PERFORMANCE TEST REPORT")
        print("="*80)

        duration = (results.end_time - results.start_time).total_seconds()

        print(f"⏱️ Test Duration: {duration:.1f} seconds")
        print(f"👥 Concurrent Users: {CONCURRENT_USERS}")
        print(f"📨 Total Requests: {results.requests_total}")
        print(f"✅ Successful Requests: {results.requests_successful}")
        print(f"❌ Failed Requests: {results.requests_failed}")
        print(f"📈 Success Rate: {results.success_rate:.2%}")
        print(f"⚡ Throughput: {results.throughput:.2f} req/s")

        if results.response_times:
            print(f"\n⏱️ Response Times:")
            print(f"  Average: {results.avg_response_time:.3f}s")
            print(f"  P95: {results.p95_response_time:.3f}s")
            print(f"  P99: {results.p99_response_time:.3f}s")
            print(f"  Min: {min(results.response_times):.3f}s")
            print(f"  Max: {max(results.response_times):.3f}s")

        if results.errors:
            print(f"\n❌ Top Errors:")
            error_counts = {}
            for error in results.errors[:20]:  # Top 20 errors
                error_counts[error] = error_counts.get(error, 0) + 1

            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {count}x: {error[:100]}...")

        # SLO Validation
        print(f"\n🎯 SLO Validation:")
        slo_status = []

        # Availability SLO: 99.9%
        if results.success_rate >= 0.999:
            slo_status.append("✅ Availability: 99.9% (PASSED)")
        else:
            slo_status.append(f"❌ Availability: {results.success_rate:.3%} (FAILED - Target: 99.9%)")

        # Latency SLO: P95 < 500ms
        if results.p95_response_time <= 0.5:
            slo_status.append("✅ Latency P95: <500ms (PASSED)")
        else:
            slo_status.append(f"❌ Latency P95: {results.p95_response_time:.3f}s (FAILED - Target: <500ms)")

        # Throughput SLO: > 100 req/s
        if results.throughput >= 100:
            slo_status.append("✅ Throughput: >100 req/s (PASSED)")
        else:
            slo_status.append(f"❌ Throughput: {results.throughput:.1f} req/s (FAILED - Target: >100 req/s)")

        for status in slo_status:
            print(f"  {status}")

        # Performance Analysis
        print(f"\n🔍 Performance Analysis:")

        if results.success_rate >= 0.95:
            print("✅ Overall performance: EXCELLENT")
        elif results.success_rate >= 0.90:
            print("⚠️ Overall performance: GOOD (minor issues)")
        else:
            print("❌ Overall performance: POOR (significant issues)")

        # Recommendations
        recommendations = []

        if results.avg_response_time > 1.0:
            recommendations.append("Consider optimizing database queries or adding caching")
        if results.p95_response_time > 2.0:
            recommendations.append("Implement request queuing or increase instance size")
        if results.success_rate < 0.99:
            recommendations.append("Investigate error patterns and improve error handling")
        if results.throughput < 50:
            recommendations.append("Consider horizontal scaling or performance optimization")

        if recommendations:
            print("💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")

        print("\n" + "="*80)

        # Sauvegarder résultats détaillés
        self.save_detailed_results(results)

    def save_detailed_results(self, results: LoadTestResult):
        """Sauvegarder résultats détaillés pour analyse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Créer dossier résultats
        os.makedirs("test-results", exist_ok=True)

        # Résultats JSON
        result_data = {
            "test_config": {
                "concurrent_users": CONCURRENT_USERS,
                "duration_seconds": DURATION_SECONDS,
                "ramp_up_time": RAMP_UP_TIME,
                "api_url": SCORING_API_URL
            },
            "summary": {
                "total_requests": results.requests_total,
                "successful_requests": results.requests_successful,
                "failed_requests": results.requests_failed,
                "success_rate": results.success_rate,
                "throughput": results.throughput,
                "avg_response_time": results.avg_response_time,
                "p95_response_time": results.p95_response_time,
                "p99_response_time": results.p99_response_time,
                "start_time": results.start_time.isoformat(),
                "end_time": results.end_time.isoformat()
            },
            "response_times": results.response_times,
            "errors": results.errors[:100],  # Limiter taille
            "system_metrics": {
                "cpu_usage": self.monitor.cpu_usage,
                "memory_usage": self.monitor.memory_usage,
                "timestamps": [t.isoformat() for t in self.monitor.timestamps]
            }
        }

        with open(f"test-results/load-test-{timestamp}.json", 'w') as f:
            json.dump(result_data, f, indent=2, default=str)

        print(f"📁 Detailed results saved to: test-results/load-test-{timestamp}.json")

async def main():
    """Fonction principale"""
    print("🔬 MLOps Scoring Platform - Load Testing")
    print("="*50)

    tester = LoadTester()

    try:
        # Initialiser session
        await tester.init_session()

        # Exécuter test
        results = await tester.run_load_test()

        # Générer rapport
        tester.generate_report(results)

    finally:
        await tester.close_session()

if __name__ == "__main__":
    # Configuration depuis variables d'environnement
    SCORING_API_URL = os.getenv("SCORING_API_URL", "http://localhost:8000")
    CONCURRENT_USERS = int(os.getenv("CONCURRENT_USERS", "50"))
    DURATION_SECONDS = int(os.getenv("DURATION_SECONDS", "300"))

    # Exécuter test
    asyncio.run(main())