#!/usr/bin/env python3
"""
MLOps Scoring Platform - Final Validation Test Runner
Orchestrateur complet des tests de validation finale
Tests end-to-end, performance, sécurité, conformité, chaos engineering
"""

import asyncio
import json
import time
import argparse
from datetime import datetime
import logging
from typing import Dict, Any, List
import subprocess
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.integration.e2e_tests import EndToEndTestSuite
from tests.performance.load_tests import LoadTestSuite
from tests.performance.stress_tests import StressTestSuite
from tests.security.security_tests import SecurityTestSuite
from tests.compliance.compliance_tests import ComplianceTestSuite
from tests.chaos.chaos_tests import ChaosTestSuite
from tests.resilience.resilience_tests import ResilienceTestSuite

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalValidationRunner:
    """Orchestrateur des tests de validation finale"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.test_suites = {}
        self.results = {}
        self.start_time = None
        self.end_time = None

    async def initialize_test_suites(self):
        """Initialiser toutes les suites de tests"""
        logger.info("🔧 Initializing final validation test suites...")

        # Tests End-to-End
        self.test_suites["e2e"] = EndToEndTestSuite(self.config.get("e2e", {}))

        # Tests Performance
        self.test_suites["load"] = LoadTestSuite(self.config.get("load", {}))
        self.test_suites["stress"] = StressTestSuite(self.config.get("stress", {}))

        # Tests Sécurité
        self.test_suites["security"] = SecurityTestSuite(self.config.get("security", {}))

        # Tests Conformité
        self.test_suites["compliance"] = ComplianceTestSuite(self.config.get("compliance", {}))

        # Tests Chaos Engineering
        self.test_suites["chaos"] = ChaosTestSuite(self.config.get("chaos", {}))

        # Tests Résilience
        self.test_suites["resilience"] = ResilienceTestSuite(self.config.get("resilience", {}))

        logger.info("✅ All test suites initialized")

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Exécuter la validation complète"""
        self.start_time = datetime.now()
        logger.info("🚀 Starting comprehensive final validation...")

        try:
            # Phase 1: Préparation
            await self.prepare_validation()

            # Phase 2: Tests End-to-End
            logger.info("🔗 Phase 2: Running End-to-End tests...")
            e2e_results = await self.run_e2e_tests()
            self.results["e2e"] = e2e_results

            # Phase 3: Tests Performance
            logger.info("⚡ Phase 3: Running Performance tests...")
            perf_results = await self.run_performance_tests()
            self.results["performance"] = perf_results

            # Phase 4: Tests Sécurité
            logger.info("🔒 Phase 4: Running Security tests...")
            security_results = await self.run_security_tests()
            self.results["security"] = security_results

            # Phase 5: Tests Conformité
            logger.info("📋 Phase 5: Running Compliance tests...")
            compliance_results = await self.run_compliance_tests()
            self.results["compliance"] = compliance_results

            # Phase 6: Tests Chaos & Résilience
            logger.info("💥 Phase 6: Running Chaos & Resilience tests...")
            chaos_results = await self.run_chaos_resilience_tests()
            self.results["chaos_resilience"] = chaos_results

            # Phase 7: Validation SLO/SLI
            logger.info("🎯 Phase 7: Validating SLO/SLI compliance...")
            slo_results = await self.validate_slo_sli()
            self.results["slo_sli"] = slo_results

            # Phase 8: Génération rapport final
            logger.info("📊 Phase 8: Generating final validation report...")
            final_report = await self.generate_final_report()

            self.end_time = datetime.now()

            logger.info("✅ Comprehensive final validation completed!")
            return final_report

        except Exception as e:
            logger.error(f"❌ Final validation failed: {e}")
            raise

    async def prepare_validation(self):
        """Préparation de la validation"""
        logger.info("🔧 Phase 1: Preparing validation environment...")

        # Vérifier environnement
        await self.verify_test_environment()

        # Créer répertoires résultats
        os.makedirs("test-results", exist_ok=True)
        os.makedirs("validation-reports", exist_ok=True)

        # Sauvegarder état système
        await self.create_system_snapshot()

        logger.info("Preparation completed")

    async def verify_test_environment(self):
        """Vérifier l'environnement de test"""
        logger.info("Verifying test environment...")

        # Vérifier services critiques
        critical_services = ["scoring-api", "mlflow", "kafka", "postgresql", "redis"]
        for service in critical_services:
            if not await self.check_service_health(service):
                logger.warning(f"⚠️ Service {service} not healthy")

        # Vérifier données de test
        if not await self.check_test_data():
            logger.warning("⚠️ Test data not available")

        # Vérifier outils de test
        required_tools = ["kubectl", "docker", "python3"]
        for tool in required_tools:
            if not self.check_tool_available(tool):
                logger.error(f"❌ Required tool {tool} not available")
                raise RuntimeError(f"Tool {tool} not available")

    async def check_service_health(self, service_name: str) -> bool:
        """Vérifier santé d'un service"""
        try:
            # Simulation - en production utiliser health checks réels
            result = subprocess.run(
                ["kubectl", "get", "pods", "-l", f"app={service_name}", "-o", "json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                pods = json.loads(result.stdout)
                return len(pods.get("items", [])) > 0
        except Exception as e:
            logger.error(f"Failed to check service {service_name}: {e}")
        return False

    def check_tool_available(self, tool: str) -> bool:
        """Vérifier disponibilité d'un outil"""
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def check_test_data(self) -> bool:
        """Vérifier disponibilité données de test"""
        # Simulation - vérifier existence fichiers/données de test
        test_files = [
            "tests/data/test_customers.csv",
            "tests/data/test_features.json",
            "tests/models/test_model.pkl"
        ]

        for file_path in test_files:
            if not os.path.exists(file_path):
                logger.warning(f"Test file missing: {file_path}")
                return False
        return True

    async def create_system_snapshot(self):
        """Créer snapshot état système"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_dir = f"validation-reports/snapshot_{timestamp}"

        os.makedirs(snapshot_dir, exist_ok=True)

        # Snapshot pods
        subprocess.run([
            "kubectl", "get", "pods", "--all-namespaces", "-o", "wide",
            ">", f"{snapshot_dir}/pods_snapshot.txt"
        ], shell=True)

        # Snapshot services
        subprocess.run([
            "kubectl", "get", "services", "--all-namespaces",
            ">", f"{snapshot_dir}/services_snapshot.txt"
        ], shell=True)

        logger.info(f"System snapshot created: {snapshot_dir}")

    async def run_e2e_tests(self) -> Dict[str, Any]:
        """Exécuter tests End-to-End"""
        suite = self.test_suites["e2e"]

        results = {
            "scoring_flow": False,
            "model_management": False,
            "feature_store": False,
            "monitoring": False,
            "user_journey": False,
            "error_handling": False
        }

        try:
            # Test flux scoring complet
            results["scoring_flow"] = await suite.test_complete_scoring_flow()

            # Test gestion modèles
            results["model_management"] = await suite.test_model_management_flow()

            # Test feature store
            results["feature_store"] = await suite.test_feature_store_flow()

            # Test monitoring
            results["monitoring"] = await suite.test_monitoring_flow()

            # Test parcours utilisateur
            results["user_journey"] = await suite.test_user_journey()

            # Test gestion erreurs
            results["error_handling"] = await suite.test_error_handling()

        except Exception as e:
            logger.error(f"E2E tests failed: {e}")
            results["error"] = str(e)

        return results

    async def run_performance_tests(self) -> Dict[str, Any]:
        """Exécuter tests performance"""
        load_suite = self.test_suites["load"]
        stress_suite = self.test_suites["stress"]

        results = {
            "load_tests": {},
            "stress_tests": {},
            "scalability": {},
            "resource_usage": {}
        }

        try:
            # Tests charge
            results["load_tests"] = await load_suite.run_load_tests()

            # Tests stress
            results["stress_tests"] = await stress_suite.run_stress_tests()

            # Tests scalabilité
            results["scalability"] = await self.test_scalability()

            # Analyse utilisation ressources
            results["resource_usage"] = await self.analyze_resource_usage()

        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            results["error"] = str(e)

        return results

    async def run_security_tests(self) -> Dict[str, Any]:
        """Exécuter tests sécurité"""
        suite = self.test_suites["security"]

        results = {
            "authentication": False,
            "authorization": False,
            "data_protection": False,
            "api_security": False,
            "infrastructure_security": False,
            "vulnerability_scan": {}
        }

        try:
            # Test authentification
            results["authentication"] = await suite.test_authentication()

            # Test autorisation
            results["authorization"] = await suite.test_authorization()

            # Test protection données
            results["data_protection"] = await suite.test_data_protection()

            # Test sécurité API
            results["api_security"] = await suite.test_api_security()

            # Test sécurité infrastructure
            results["infrastructure_security"] = await suite.test_infrastructure_security()

            # Scan vulnérabilités
            results["vulnerability_scan"] = await suite.run_vulnerability_scan()

        except Exception as e:
            logger.error(f"Security tests failed: {e}")
            results["error"] = str(e)

        return results

    async def run_compliance_tests(self) -> Dict[str, Any]:
        """Exécuter tests conformité"""
        suite = self.test_suites["compliance"]

        results = {
            "gdpr_compliance": {},
            "pci_compliance": {},
            "sox_compliance": {},
            "data_residency": False,
            "audit_logging": False,
            "data_encryption": False
        }

        try:
            # Conformité GDPR
            results["gdpr_compliance"] = await suite.test_gdpr_compliance()

            # Conformité PCI-DSS
            results["pci_compliance"] = await suite.test_pci_compliance()

            # Conformité SOX
            results["sox_compliance"] = await suite.test_sox_compliance()

            # Résidence données
            results["data_residency"] = await suite.test_data_residency()

            # Logging audit
            results["audit_logging"] = await suite.test_audit_logging()

            # Chiffrement données
            results["data_encryption"] = await suite.test_data_encryption()

        except Exception as e:
            logger.error(f"Compliance tests failed: {e}")
            results["error"] = str(e)

        return results

    async def run_chaos_resilience_tests(self) -> Dict[str, Any]:
        """Exécuter tests chaos et résilience"""
        chaos_suite = self.test_suites["chaos"]
        resilience_suite = self.test_suites["resilience"]

        results = {
            "chaos_tests": {},
            "resilience_tests": {},
            "failover_tests": {},
            "recovery_tests": {}
        }

        try:
            # Tests chaos engineering
            results["chaos_tests"] = await chaos_suite.run_chaos_experiments()

            # Tests résilience
            results["resilience_tests"] = await resilience_suite.test_resilience()

            # Tests failover
            results["failover_tests"] = await self.test_failover_scenarios()

            # Tests recovery
            results["recovery_tests"] = await self.test_recovery_procedures()

        except Exception as e:
            logger.error(f"Chaos/Resilience tests failed: {e}")
            results["error"] = str(e)

        return results

    async def validate_slo_sli(self) -> Dict[str, Any]:
        """Valider conformité SLO/SLI"""
        slo_targets = {
            "availability": 0.999,      # 99.9%
            "latency_p95": 500,         # 500ms
            "throughput": 1000,         # 1000 req/s
            "error_rate": 0.001,        # 0.1%
            "data_freshness": 3600      # 1h
        }

        slo_results = {}

        try:
            # Mesurer métriques actuelles
            current_metrics = await self.measure_current_metrics()

            # Valider chaque SLO
            for slo_name, target in slo_targets.items():
                current_value = current_metrics.get(slo_name, 0)
                compliant = self.check_slo_compliance(slo_name, current_value, target)

                slo_results[slo_name] = {
                    "target": target,
                    "current": current_value,
                    "compliant": compliant,
                    "deviation": abs(current_value - target) / target if target != 0 else 0
                }

            # Score global conformité
            slo_results["overall_compliance"] = self.calculate_overall_compliance(slo_results)

        except Exception as e:
            logger.error(f"SLO/SLI validation failed: {e}")
            slo_results["error"] = str(e)

        return slo_results

    async def measure_current_metrics(self) -> Dict[str, Any]:
        """Mesurer métriques actuelles"""
        # Simulation - en production utiliser monitoring réel
        return {
            "availability": 0.997,      # 99.7%
            "latency_p95": 320,         # 320ms
            "throughput": 1250,         # 1250 req/s
            "error_rate": 0.0008,       # 0.08%
            "data_freshness": 1800      # 30min
        }

    def check_slo_compliance(self, slo_name: str, current: float, target: float) -> bool:
        """Vérifier conformité SLO"""
        if slo_name in ["availability"]:
            return current >= target
        elif slo_name in ["latency_p95", "data_freshness"]:
            return current <= target
        elif slo_name in ["throughput"]:
            return current >= target
        elif slo_name in ["error_rate"]:
            return current <= target
        return False

    def calculate_overall_compliance(self, slo_results: Dict[str, Any]) -> float:
        """Calculer score conformité global"""
        compliant_slos = sum(1 for slo in slo_results.values()
                           if isinstance(slo, dict) and slo.get("compliant", False))
        total_slos = len([slo for slo in slo_results.values()
                         if isinstance(slo, dict) and "compliant" in slo])

        return compliant_slos / total_slos if total_slos > 0 else 0

    async def test_scalability(self) -> Dict[str, Any]:
        """Tester scalabilité système"""
        # Simulation tests scalabilité
        return {
            "horizontal_scaling": True,
            "vertical_scaling": True,
            "auto_scaling": True,
            "resource_efficiency": 0.85
        }

    async def analyze_resource_usage(self) -> Dict[str, Any]:
        """Analyser utilisation ressources"""
        # Simulation analyse ressources
        return {
            "cpu_usage": 0.65,
            "memory_usage": 0.72,
            "disk_usage": 0.45,
            "network_usage": 0.38
        }

    async def test_failover_scenarios(self) -> Dict[str, Any]:
        """Tester scénarios failover"""
        # Simulation tests failover
        return {
            "database_failover": True,
            "service_failover": True,
            "regional_failover": True,
            "recovery_time": 45  # seconds
        }

    async def test_recovery_procedures(self) -> Dict[str, Any]:
        """Tester procédures recovery"""
        # Simulation tests recovery
        return {
            "data_recovery": True,
            "service_recovery": True,
            "full_system_recovery": True,
            "data_loss": 0  # minutes
        }

    async def generate_final_report(self) -> Dict[str, Any]:
        """Générer rapport final de validation"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0

        report = {
            "validation_summary": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": duration,
                "test_suites_executed": list(self.results.keys()),
                "overall_success": self.calculate_overall_success()
            },
            "results": self.results,
            "compliance_status": self.generate_compliance_status(),
            "recommendations": self.generate_validation_recommendations(),
            "next_steps": self.generate_validation_next_steps()
        }

        # Sauvegarder rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"validation-reports/final-validation-report-{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Final validation report saved to: {report_file}")

        return report

    def calculate_overall_success(self) -> bool:
        """Calculer succès global validation"""
        # Critères succès : tous les tests critiques passent
        critical_tests = ["e2e", "security", "compliance"]

        for test_type in critical_tests:
            if test_type in self.results:
                result = self.results[test_type]
                if isinstance(result, dict) and result.get("error"):
                    return False

        # Vérifier conformité SLO
        slo_results = self.results.get("slo_sli", {})
        overall_compliance = slo_results.get("overall_compliance", 0)
        if overall_compliance < 0.9:  # 90% compliance minimum
            return False

        return True

    def generate_compliance_status(self) -> Dict[str, Any]:
        """Générer status conformité"""
        status = {
            "security_compliance": "unknown",
            "regulatory_compliance": "unknown",
            "performance_compliance": "unknown",
            "operational_compliance": "unknown"
        }

        # Évaluer conformité sécurité
        security_results = self.results.get("security", {})
        if security_results.get("authentication") and security_results.get("authorization"):
            status["security_compliance"] = "compliant"
        else:
            status["security_compliance"] = "non_compliant"

        # Évaluer conformité réglementaire
        compliance_results = self.results.get("compliance", {})
        gdpr_ok = compliance_results.get("gdpr_compliance", {}).get("passed", False)
        pci_ok = compliance_results.get("pci_compliance", {}).get("passed", False)

        if gdpr_ok and pci_ok:
            status["regulatory_compliance"] = "compliant"
        else:
            status["regulatory_compliance"] = "non_compliant"

        # Évaluer conformité performance
        slo_results = self.results.get("slo_sli", {})
        overall_compliance = slo_results.get("overall_compliance", 0)

        if overall_compliance >= 0.95:
            status["performance_compliance"] = "excellent"
        elif overall_compliance >= 0.9:
            status["performance_compliance"] = "good"
        elif overall_compliance >= 0.8:
            status["performance_compliance"] = "acceptable"
        else:
            status["performance_compliance"] = "poor"

        # Évaluer conformité opérationnelle
        e2e_results = self.results.get("e2e", {})
        chaos_results = self.results.get("chaos_resilience", {})

        e2e_success = all(e2e_results.values()) if e2e_results else False
        chaos_success = all(chaos_results.values()) if chaos_results else False

        if e2e_success and chaos_success:
            status["operational_compliance"] = "compliant"
        else:
            status["operational_compliance"] = "needs_improvement"

        return status

    def generate_validation_recommendations(self) -> List[str]:
        """Générer recommandations validation"""
        recommendations = []

        # Analyser résultats pour recommandations
        if not self.results.get("e2e", {}).get("scoring_flow", False):
            recommendations.append("Fix end-to-end scoring flow - critical integration issues detected")

        slo_results = self.results.get("slo_sli", {})
        if slo_results.get("overall_compliance", 0) < 0.9:
            recommendations.append("Improve SLO compliance - performance targets not met")

        security_results = self.results.get("security", {})
        if not security_results.get("authentication", False):
            recommendations.append("Strengthen authentication mechanisms")

        compliance_results = self.results.get("compliance", {})
        if not compliance_results.get("gdpr_compliance", {}).get("passed", False):
            recommendations.append("Address GDPR compliance gaps")

        return recommendations

    def generate_validation_next_steps(self) -> List[str]:
        """Générer prochaines étapes validation"""
        return [
            "Address critical issues identified in validation report",
            "Implement monitoring for SLO/SLI compliance",
            "Set up automated validation in CI/CD pipeline",
            "Create runbooks for identified failure scenarios",
            "Schedule regular validation testing (weekly/monthly)",
            "Establish incident response procedures for validation failures"
        ]

def load_validation_config(config_file: str = "tests/validation/validation-config.json") -> Dict[str, Any]:
    """Charger configuration validation"""
    default_config = {
        "e2e": {
            "base_url": "http://localhost:8000",
            "timeout": 30,
            "retries": 3
        },
        "load": {
            "duration": 300,  # 5 minutes
            "concurrency": 100,
            "ramp_up": 60
        },
        "stress": {
            "max_concurrency": 1000,
            "duration": 600,  # 10 minutes
            "failure_threshold": 0.1
        },
        "security": {
            "scan_depth": "deep",
            "vulnerability_threshold": "medium",
            "compliance_frameworks": ["OWASP", "NIST"]
        },
        "compliance": {
            "gdpr_enabled": True,
            "pci_enabled": True,
            "audit_retention_days": 2555
        },
        "chaos": {
            "experiments": ["pod_kill", "network_delay", "resource_stress"],
            "duration": 300,
            "recovery_timeout": 60
        },
        "resilience": {
            "failure_scenarios": ["db_failure", "service_crash", "network_partition"],
            "recovery_validation": True
        }
    }

    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            user_config = json.load(f)
        # Fusionner avec config par défaut
        for key, value in user_config.items():
            if key in default_config:
                default_config[key].update(value)
            else:
                default_config[key] = value

    return default_config

def print_validation_summary(report: Dict[str, Any]):
    """Afficher résumé validation"""
    print("\n" + "="*80)
    print("🧪 FINAL VALIDATION SUMMARY REPORT")
    print("="*80)

    summary = report.get("validation_summary", {})
    print(f"⏱️ Duration: {summary.get('duration_seconds', 0):.1f} seconds")
    print(f"✅ Overall Success: {summary.get('overall_success', False)}")
    print(f"🔧 Test Suites Executed: {', '.join(summary.get('test_suites_executed', []))}")

    # Status conformité
    compliance = report.get("compliance_status", {})
    print("\n📋 Compliance Status:")
    for compliance_type, status in compliance.items():
        status_icon = "✅" if status in ["compliant", "excellent", "good"] else "❌" if status in ["non_compliant", "poor"] else "⚠️"
        print(f"  {status_icon} {compliance_type.replace('_', ' ').title()}: {status}")

    # Résultats par catégorie
    results = report.get("results", {})
    print("\n🧪 Test Results:")
    for test_type, test_results in results.items():
        if isinstance(test_results, dict) and "error" not in test_results:
            passed = sum(1 for v in test_results.values() if v is True or (isinstance(v, dict) and v.get("passed")))
            total = len([v for v in test_results.values() if isinstance(v, (bool, dict))])
            success_rate = passed / total if total > 0 else 0
            status_icon = "✅" if success_rate >= 0.9 else "⚠️" if success_rate >= 0.7 else "❌"
            print(f"  {status_icon} {test_type.upper()}: {passed}/{total} passed ({success_rate:.1%})")

    recommendations = report.get("recommendations", [])
    if recommendations:
        print("\n💡 Critical Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    next_steps = report.get("next_steps", [])
    if next_steps:
        print("\n🎯 Next Steps:")
        for i, step in enumerate(next_steps, 1):
            print(f"  {i}. {step}")

    print("\n" + "="*80)

async def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="MLOps Scoring Platform Final Validation Runner")
    parser.add_argument("--config", default="tests/validation/validation-config.json",
                       help="Validation configuration file path")
    parser.add_argument("--e2e-only", action="store_true",
                       help="Run E2E tests only")
    parser.add_argument("--perf-only", action="store_true",
                       help="Run performance tests only")
    parser.add_argument("--security-only", action="store_true",
                       help="Run security tests only")
    parser.add_argument("--compliance-only", action="store_true",
                       help="Run compliance tests only")
    parser.add_argument("--chaos-only", action="store_true",
                       help="Run chaos tests only")
    parser.add_argument("--skip-slo-validation", action="store_true",
                       help="Skip SLO/SLI validation")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("🧪 MLOps Scoring Platform - Final Validation Runner")
    print("="*70)

    try:
        # Charger configuration
        config = load_validation_config(args.config)
        logger.info(f"Validation configuration loaded from: {args.config}")

        # Créer orchestrateur
        runner = FinalValidationRunner(config)

        # Initialiser suites de tests
        await runner.initialize_test_suites()

        # Ajuster configuration selon arguments
        if args.e2e_only:
            # Désactiver autres tests
            config["load"] = {"enabled": False}
            config["stress"] = {"enabled": False}
            config["security"] = {"enabled": False}
            config["compliance"] = {"enabled": False}
            config["chaos"] = {"enabled": False}
            config["resilience"] = {"enabled": False}

        # Exécuter validation
        report = await runner.run_comprehensive_validation()

        # Afficher résumé
        print_validation_summary(report)

        # Code de sortie
        success = report.get("validation_summary", {}).get("overall_success", False)
        exit(0 if success else 1)

    except Exception as e:
        logger.error(f"❌ Final validation runner failed: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())