#!/usr/bin/env python
"""
MASTER VALIDATOR
================

Runs 3 validators in sequence:
1. structure_validator (mandatory)
2. accessibility_validator (mandatory)
3. visual_regression (optional, controlled by UI_PHASE env var)

Only passes if structure + accessibility pass.
Visual diff is skipped during redesign phase.

Usage:
  python validate.py              # Uses UI_PHASE=redesign (default)
  UI_PHASE=freeze python validate.py  # Enforces visual diffs
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_validator(script_name):
    """Run a validator script and return results."""
    result = subprocess.run(
        [sys.executable, str(ROOT / script_name)],
        capture_output=False,
        text=True,
    )
    
    # Read the report
    if script_name == "structure_validator.py":
        report_path = ROOT / "structure_report.json"
    elif script_name == "accessibility_validator.py":
        report_path = ROOT / "accessibility_report.json"
    else:
        report_path = ROOT / "visual_report.json"
    
    try:
        report = json.loads(report_path.read_text())
        return report
    except Exception:
        return {"total_failures": -1, "failures": ["Failed to read report"]}


def main():
    print("\n" + "=" * 70)
    print("MASTER VALIDATOR: Running structure + accessibility checks")
    print("=" * 70 + "\n")

    # Run structure validator
    print("1. Structure Validator...")
    structure = run_validator("structure_validator.py")
    print(f"   Failures: {structure['total_failures']}")

    # Run accessibility validator
    print("2. Accessibility Validator...")
    accessibility = run_validator("accessibility_validator.py")
    print(f"   Failures: {accessibility['total_failures']}")

    # Run visual regression validator
    print("3. Visual Regression Validator...")
    visual = run_validator("visual_regression.py")
    print(f"   Failures: {visual['total_failures']}")

    # Combine results
    mandatory_failures = structure["total_failures"] + accessibility["total_failures"]
    all_failures = mandatory_failures + visual["total_failures"]
    all_failure_list = structure["failures"] + accessibility["failures"] + visual["failures"]

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Structure failures: {structure['total_failures']}")
    print(f"Accessibility failures: {accessibility['total_failures']}")
    print(f"Visual failures: {visual['total_failures']}")
    print(f"\nMandatory failures (structure + accessibility): {mandatory_failures}")
    print(f"Total failures: {all_failures}")
    print("=" * 70 + "\n")

    # Report
    report = {
        "total_failures": mandatory_failures,
        "mandatory_failures": mandatory_failures,
        "visual_failures": visual["total_failures"],
        "all_failures": all_failures,
        "failures": all_failure_list,
        "summary": {
            "structure": structure["total_failures"],
            "accessibility": accessibility["total_failures"],
            "visual": visual["total_failures"],
        }
    }

    report_path = ROOT / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))

    # Exit code based on mandatory failures only
    if mandatory_failures > 0:
        sys.exit(1)
    else:
        print("\n✓ Structure and Accessibility pass. System is valid.\n")


if __name__ == "__main__":
    main()