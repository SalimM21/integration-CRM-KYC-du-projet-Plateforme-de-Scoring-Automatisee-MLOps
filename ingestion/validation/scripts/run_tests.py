"""
Script pour exécuter les tests avec rapport de couverture
"""
import pytest
import coverage
import os
import sys
from pathlib import Path

def run_tests_with_coverage():
    """Exécute les tests avec rapport de couverture"""
    # Configuration de la couverture
    cov = coverage.Coverage(
        branch=True,
        source=['validation'],
        omit=['*/__init__.py', '*/tests/*'],
        config_file=False
    )
    
    # Démarrage de la couverture
    cov.start()
    
    # Exécution des tests
    test_path = Path(__file__).parent.parent
    pytest_args = [
        '-v',
        '--tb=short',
        f'{test_path}/tests',
        '-p', 'no:warnings'
    ]
    
    print("Exécution des tests...")
    result = pytest.main(pytest_args)
    
    # Arrêt de la couverture
    cov.stop()
    
    # Génération des rapports
    print("\nRapport de couverture :")
    cov.report()
    
    # Génération du rapport HTML
    reports_dir = Path(__file__).parent.parent / 'reports' / 'coverage'
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    cov.html_report(directory=str(reports_dir))
    print(f"\nRapport HTML détaillé généré dans : {reports_dir}")
    
    return result

if __name__ == '__main__':
    sys.exit(run_tests_with_coverage())