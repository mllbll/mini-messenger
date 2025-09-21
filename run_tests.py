#!/usr/bin/env python3
"""
Test runner script for mini-messenger.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def run_unit_tests():
    """Run unit tests."""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    return run_command("python -m pytest tests/unit/ -v --tb=short")


def run_integration_tests():
    """Run integration tests."""
    print("=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    return run_command("python -m pytest tests/integration/ -v --tb=short")


def run_security_tests():
    """Run security tests."""
    print("=" * 60)
    print("RUNNING SECURITY TESTS")
    print("=" * 60)
    
    return run_command("python -m pytest tests/security/ -v --tb=short")


def run_load_tests():
    """Run load tests."""
    print("=" * 60)
    print("RUNNING LOAD TESTS")
    print("=" * 60)
    
    # Run custom load test runner
    success1 = run_command("python tests/load/load_test_runner.py")
    
    # Run Locust tests (if available)
    success2 = run_command("locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 30s --html load_test_report.html")
    
    return success1 and success2


def run_frontend_tests():
    """Run frontend tests."""
    print("=" * 60)
    print("RUNNING FRONTEND TESTS")
    print("=" * 60)
    
    # Check if Selenium is available
    try:
        import selenium
        return run_command("python -m pytest tests/frontend/ -v --tb=short")
    except ImportError:
        print("Selenium not available. Install with: pip install selenium")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)
    
    results = []
    
    # Run tests in order
    results.append(("Unit Tests", run_unit_tests()))
    results.append(("Integration Tests", run_integration_tests()))
    results.append(("Security Tests", run_security_tests()))
    results.append(("Load Tests", run_load_tests()))
    results.append(("Frontend Tests", run_frontend_tests()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! 🎉")
    else:
        print("SOME TESTS FAILED! ❌")
    
    return all_passed


def run_coverage_report():
    """Run tests with coverage report."""
    print("=" * 60)
    print("RUNNING TESTS WITH COVERAGE")
    print("=" * 60)
    
    return run_command("python -m pytest tests/ --cov=backend/app --cov-report=html --cov-report=term-missing")


def setup_test_environment():
    """Set up test environment."""
    print("=" * 60)
    print("SETTING UP TEST ENVIRONMENT")
    print("=" * 60)
    
    # Install test dependencies
    success = run_command("pip install -r tests/requirements.txt")
    
    if success:
        print("Test dependencies installed successfully!")
    else:
        print("Failed to install test dependencies!")
    
    return success


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests for mini-messenger")
    parser.add_argument("--type", choices=["unit", "integration", "security", "load", "frontend", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--setup", action="store_true", help="Set up test environment")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    if args.setup:
        success = setup_test_environment()
        sys.exit(0 if success else 1)
    
    # Run tests
    if args.coverage:
        success = run_coverage_report()
    elif args.type == "unit":
        success = run_unit_tests()
    elif args.type == "integration":
        success = run_integration_tests()
    elif args.type == "security":
        success = run_security_tests()
    elif args.type == "load":
        success = run_load_tests()
    elif args.type == "frontend":
        success = run_frontend_tests()
    else:  # all
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
