#!/usr/bin/env python3
"""
Build-time health checks for Cafe Fusion application.
Run this script before starting the application to ensure all services are ready.
"""

import sys
import os
import json
from datetime import datetime

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from health_checks import get_overall_health, HealthCheckResult


def print_check_result(check: HealthCheckResult):
    """Print the result of a health check in a formatted way."""
    status = "PASS" if check.status else "FAIL"
    color_code = "\033[92m" if check.status else "\033[91m"  # Green for pass, red for fail
    print(f"{color_code}[{status}]\033[0m {check.service_name.upper()}: {check.message}")
    
    if check.details:
        print("  Details:")
        for key, value in check.details.items():
            print(f"    {key}: {json.dumps(value, default=str)}")
    print()


def run_build_checks(verbose: bool = False):
    """Run all build-time checks and return the overall status."""
    print("=" * 60)
    print("Cafe Fusion - Build Health Checks")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Create app context
    app = create_app()
    all_passed = True
    
    with app.app_context():
        health_status = get_overall_health()
        
        # Print results
        for check in health_status["checks"]:
            print_check_result(check)
            if not check.status:
                all_passed = False
        
        # Print summary
        print("=" * 60)
        if all_passed:
            print("✓ All checks passed!")
        else:
            print(f"✗ {health_status['failed_count']} of {health_status['total_count']} checks failed")
        
        print(f"Status: {'HEALTHY' if all_passed else 'UNHEALTHY'}")
        print("=" * 60)
        
        return all_passed


if __name__ == "__main__":
    try:
        success = run_build_checks(verbose=True)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR] Failed to run health checks: {str(e)}")
        sys.exit(1)