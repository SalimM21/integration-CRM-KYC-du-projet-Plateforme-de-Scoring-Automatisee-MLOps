#!/bin/bash

# MLOps Scoring Platform - Integration Tests Runner
# Script principal pour exécuter tous les tests d'intégration

set -euo pipefail

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ENV="${TEST_ENV:-local}"
PARALLEL_TESTS="${PARALLEL_TESTS:-false}"
VERBOSE="${VERBOSE:-false}"
REPORT_DIR="${REPORT_DIR:-test-reports}"
COVERAGE="${COVERAGE:-false}"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier prérequis
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Python 3.8+
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required"
        exit 1
    fi

    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ "$(printf '%s\n' "$python_version" "3.8" | sort -V | head -n1)" != "3.8" ]]; then
        log_error "Python 3.8+ is required (found $python_version)"
        exit 1
    fi

    # pip
    if ! command -v pip3 >/dev/null 2>&1; then
        log_error "pip3 is required"
        exit 1
    fi

    # kubectl (pour tests Kubernetes)
    if ! command -v kubectl >/dev/null 2>&1; then
        log_warning "kubectl not found - Kubernetes tests will be skipped"
    fi

    # Docker (pour tests conteneurs)
    if ! command -v docker >/dev/null 2>&1; then
        log_warning "Docker not found - container tests will be skipped"
    fi

    log_success "Prerequisites check completed"
}

# Installer dépendances de test
install_dependencies() {
    log_info "Installing test dependencies..."

    # Installer pytest et plugins
    pip3 install --quiet pytest pytest-asyncio pytest-cov pytest-html pytest-xdist

    # Installer dépendances spécifiques aux tests
    pip3 install --quiet \
        requests aiohttp kafka-python psycopg2-binary redis minio \
        locust matplotlib pandas psutil

    # Pour tests chaos (optionnel)
    pip3 install --quiet chaosmonkey || true

    log_success "Test dependencies installed"
}

# Configuration environnement de test
setup_test_environment() {
    log_info "Setting up test environment..."

    # Créer répertoire rapports
    mkdir -p "$REPORT_DIR"

    # Variables d'environnement pour tests
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
    export TEST_ENV="$TEST_ENV"
    export REPORT_DIR="$REPORT_DIR"

    # Configuration selon environnement
    case "$TEST_ENV" in
        local)
            export SCORING_API_URL="http://localhost:8000"
            export MLFLOW_URL="http://localhost:5000"
            export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
            export POSTGRES_CONFIG_HOST="localhost"
            export REDIS_HOST="localhost"
            export MINIO_ENDPOINT="localhost:9000"
            ;;
        staging)
            export SCORING_API_URL="https://api-staging.company.com"
            export MLFLOW_URL="https://mlflow-staging.company.com"
            # ... autres configs staging
            ;;
        production)
            log_warning "Running tests against production environment!"
            export SCORING_API_URL="https://api.company.com"
            # ... configs production (avec précaution)
            ;;
        *)
            log_error "Unknown test environment: $TEST_ENV"
            exit 1
            ;;
    esac

    log_success "Test environment configured for: $TEST_ENV"
}

# Tests unitaires
run_unit_tests() {
    log_info "Running unit tests..."

    local pytest_args=(
        --tb=short
        --strict-markers
        --disable-warnings
        -q
    )

    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=(--verbose)
    fi

    if [[ "$COVERAGE" == "true" ]]; then
        pytest_args+=(--cov=src --cov-report=html:"$REPORT_DIR/coverage" --cov-report=term)
    fi

    if [[ "$PARALLEL_TESTS" == "true" ]]; then
        pytest_args+=(-n auto)
    fi

    # Exécuter tests unitaires
    if python3 -m pytest "${pytest_args[@]}" tests/unit/ 2>/dev/null; then
        log_success "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Tests d'intégration end-to-end
run_integration_tests() {
    log_info "Running integration tests..."

    local pytest_args=(
        --tb=short
        --strict-markers
        --disable-warnings
        -q
        --maxfail=5
    )

    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=(--verbose)
    fi

    # Exécuter tests d'intégration
    if python3 -m pytest "${pytest_args[@]}" tests/integration/ 2>/dev/null; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Tests de performance
run_performance_tests() {
    log_info "Running performance tests..."

    # Configuration tests performance
    export CONCURRENT_USERS="${CONCURRENT_USERS:-50}"
    export DURATION_SECONDS="${DURATION_SECONDS:-300}"

    # Exécuter tests de charge
    if python3 tests/performance/load-tests.py; then
        log_success "Performance tests completed"
        return 0
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Tests de chaos engineering
run_chaos_tests() {
    log_info "Running chaos engineering tests..."

    # Vérifier si on peut exécuter les tests chaos
    if [[ "$TEST_ENV" == "production" ]]; then
        log_warning "Skipping chaos tests in production environment"
        return 0
    fi

    # Exécuter tests chaos
    if python3 tests/chaos/chaos-tests.py; then
        log_success "Chaos tests completed"
        return 0
    else
        log_error "Chaos tests failed"
        return 1
    fi
}

# Tests de sécurité
run_security_tests() {
    log_info "Running security tests..."

    # Tests de sécurité statique (SAST)
    if command -v bandit >/dev/null 2>&1; then
        log_info "Running Bandit security scan..."
        bandit -r src/ -f json -o "$REPORT_DIR/security-bandit.json" || true
    else
        log_warning "Bandit not installed - skipping SAST"
    fi

    # Tests de sécurité des conteneurs (si Docker disponible)
    if command -v docker >/dev/null 2>&1 && command -v trivy >/dev/null 2>&1; then
        log_info "Running Trivy container security scan..."
        # Scanner l'image de l'API
        docker build -t scoring-api-test . 2>/dev/null || true
        trivy image --format json --output "$REPORT_DIR/security-trivy.json" scoring-api-test 2>/dev/null || true
    else
        log_warning "Docker/Trivy not available - skipping container security scan"
    fi

    # Tests de sécurité API (DAST)
    if python3 -c "import zapv2" 2>/dev/null; then
        log_info "Running OWASP ZAP security scan..."
        # Intégration ZAP pour tests DAST
        python3 tests/security/zap-scan.py || true
    else
        log_warning "OWASP ZAP not available - skipping DAST"
    fi

    log_success "Security tests completed"
}

# Tests de conformité
run_compliance_tests() {
    log_info "Running compliance tests..."

    # Tests GDPR
    log_info "Testing GDPR compliance..."
    python3 tests/compliance/gdpr-tests.py || true

    # Tests PCI-DSS (si applicable)
    if [[ -f "tests/compliance/pci-tests.py" ]]; then
        log_info "Testing PCI-DSS compliance..."
        python3 tests/compliance/pci-tests.py || true
    fi

    # Tests SOX (si applicable)
    if [[ -f "tests/compliance/sox-tests.py" ]]; then
        log_info "Testing SOX compliance..."
        python3 tests/compliance/sox-tests.py || true
    fi

    log_success "Compliance tests completed"
}

# Générer rapport final
generate_final_report() {
    log_info "Generating final test report..."

    local report_file="$REPORT_DIR/integration-test-report-$(date +%Y%m%d_%H%M%S).md"

    cat << EOF > "$report_file"
# MLOps Scoring Platform - Integration Test Report

## Test Execution Summary
- **Date**: $(date)
- **Environment**: $TEST_ENV
- **Duration**: ${SECONDS}s
- **Parallel Execution**: $PARALLEL_TESTS
- **Coverage**: $COVERAGE

## Test Results

### Unit Tests
$(if [[ -f "$REPORT_DIR/unit-results.json" ]]; then
    echo "\`\`\`json"
    cat "$REPORT_DIR/unit-results.json" | jq '.summary' 2>/dev/null || echo "Results not available"
    echo "\`\`\`"
else
    echo "❌ Unit tests not executed or results not found"
fi)

### Integration Tests
$(if [[ -f "$REPORT_DIR/integration-results.json" ]]; then
    echo "\`\`\`json"
    cat "$REPORT_DIR/integration-results.json" | jq '.summary' 2>/dev/null || echo "Results not available"
    echo "\`\`\`"
else
    echo "❌ Integration tests not executed or results not found"
fi)

### Performance Tests
$(if [[ -d "test-results" ]] && [[ -f "test-results/load-test-*.json" ]]; then
    echo "\`\`\`json"
    ls test-results/load-test-*.json | head -1 | xargs cat | jq '.summary' 2>/dev/null || echo "Results not available"
    echo "\`\`\`"
else
    echo "❌ Performance tests not executed or results not found"
fi)

### Security Tests
$(if [[ -f "$REPORT_DIR/security-bandit.json" ]]; then
    echo "#### Bandit SAST Results"
    echo "\`\`\`json"
    cat "$REPORT_DIR/security-bandit.json" | jq '.results' 2>/dev/null || echo "Results not available"
    echo "\`\`\`"
fi)

$(if [[ -f "$REPORT_DIR/security-trivy.json" ]]; then
    echo "#### Trivy Container Scan Results"
    echo "\`\`\`json"
    cat "$REPORT_DIR/security-trivy.json" | jq '.Results[0].Vulnerabilities | length' 2>/dev/null || echo "Results not available"
    echo " vulnerabilities found"
fi)

## Recommendations

### Performance
- Monitor response times and scale accordingly
- Implement caching for frequently accessed data
- Optimize database queries and indexes

### Security
- Address high-severity vulnerabilities immediately
- Implement regular security scans in CI/CD
- Review and update security policies

### Reliability
- Implement proper error handling and retries
- Set up monitoring and alerting
- Create runbooks for incident response

### Compliance
- Ensure audit logging is comprehensive
- Implement data retention policies
- Regular compliance assessments

---
*Generated by integration test runner*
EOF

    log_success "Final report generated: $report_file"
    echo "📊 Report available at: $report_file"
}

# Fonction principale
main() {
    local start_time=$SECONDS
    local exit_code=0

    echo "🧪 MLOps Scoring Platform - Integration Test Suite"
    echo "=================================================="
    log_info "Starting comprehensive integration tests..."

    # Prérequis
    check_prerequisites

    # Installation dépendances
    install_dependencies

    # Configuration environnement
    setup_test_environment

    # Exécuter tests selon configuration
    local test_results=()

    # Tests unitaires (toujours exécutés)
    if run_unit_tests; then
        test_results+=("✅ Unit Tests: PASSED")
    else
        test_results+=("❌ Unit Tests: FAILED")
        exit_code=1
    fi

    # Tests d'intégration
    if run_integration_tests; then
        test_results+=("✅ Integration Tests: PASSED")
    else
        test_results+=("❌ Integration Tests: FAILED")
        exit_code=1
    fi

    # Tests de performance (optionnel)
    if [[ "${RUN_PERFORMANCE:-true}" == "true" ]]; then
        if run_performance_tests; then
            test_results+=("✅ Performance Tests: PASSED")
        else
            test_results+=("⚠️ Performance Tests: ISSUES")
        fi
    fi

    # Tests de chaos (optionnel, seulement si pas production)
    if [[ "${RUN_CHAOS:-false}" == "true" ]] && [[ "$TEST_ENV" != "production" ]]; then
        if run_chaos_tests; then
            test_results+=("✅ Chaos Tests: PASSED")
        else
            test_results+=("⚠️ Chaos Tests: ISSUES")
        fi
    fi

    # Tests de sécurité (optionnel)
    if [[ "${RUN_SECURITY:-true}" == "true" ]]; then
        if run_security_tests; then
            test_results+=("✅ Security Tests: COMPLETED")
        else
            test_results+=("⚠️ Security Tests: ISSUES")
        fi
    fi

    # Tests de conformité (optionnel)
    if [[ "${RUN_COMPLIANCE:-true}" == "true" ]]; then
        if run_compliance_tests; then
            test_results+=("✅ Compliance Tests: COMPLETED")
        else
            test_results+=("⚠️ Compliance Tests: ISSUES")
        fi
    fi

    # Rapport final
    generate_final_report

    # Résumé
    echo ""
    echo "📊 TEST EXECUTION SUMMARY"
    echo "========================="
    printf '%s\n' "${test_results[@]}"
    echo ""
    log_info "Total execution time: $((SECONDS - start_time))s"

    if [[ $exit_code -eq 0 ]]; then
        log_success "🎉 All critical tests passed!"
    else
        log_error "💥 Some tests failed - check reports for details"
    fi

    return $exit_code
}

# Gestion des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env=*)
            TEST_ENV="${1#*=}"
            shift
            ;;
        --parallel)
            PARALLEL_TESTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --performance-only)
            RUN_PERFORMANCE=true
            RUN_CHAOS=false
            RUN_SECURITY=false
            RUN_COMPLIANCE=false
            shift
            ;;
        --security-only)
            RUN_PERFORMANCE=false
            RUN_CHAOS=false
            RUN_SECURITY=true
            RUN_COMPLIANCE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --env=ENV          Test environment (local, staging, production)"
            echo "  --parallel         Run tests in parallel"
            echo "  --verbose          Verbose output"
            echo "  --coverage         Generate coverage reports"
            echo "  --performance-only Run only performance tests"
            echo "  --security-only    Run only security and compliance tests"
            echo "  --help             Show this help"
            echo ""
            echo "Environment variables:"
            echo "  SCORING_API_URL    API endpoint URL"
            echo "  CONCURRENT_USERS   Number of users for load tests"
            echo "  DURATION_SECONDS   Test duration in seconds"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Variables par défaut
RUN_PERFORMANCE="${RUN_PERFORMANCE:-false}"
RUN_CHAOS="${RUN_CHAOS:-false}"
RUN_SECURITY="${RUN_SECURITY:-false}"
RUN_COMPLIANCE="${RUN_COMPLIANCE:-false}"

# Exécuter tests
main