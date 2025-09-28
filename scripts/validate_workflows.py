#!/usr/bin/env python3
"""
Simple YAML validation for GitHub Actions workflows
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


def validate_yaml_file(file_path: str) -> bool:
    """Validate YAML syntax for a single file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            yaml.safe_load(f)
        print(f"SUCCESS: {file_path} - Valid YAML syntax")
        return True
    except yaml.YAMLError as e:
        print(f"ERROR: {file_path} - YAML syntax error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {file_path} - File error: {e}")
        return False


def validate_workflow_structure(file_path: str) -> bool:
    """Validate GitHub Actions workflow structure"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)

        # Check required fields
        required_fields = ["name", "jobs"]
        for field in required_fields:
            if field not in workflow:
                print(f"ERROR: {file_path} - Missing required field: '{field}'")
                return False

        # Check for 'on' field (can be 'on' or True due to YAML parsing)
        if "on" not in workflow and True not in workflow:
            print(f"ERROR: {file_path} - Missing required field: 'on'")
            return False

        # Check jobs structure
        if not isinstance(workflow["jobs"], dict):
            print(f"ERROR: {file_path} - 'jobs' must be a dictionary")
            return False

        # Check each job has required fields
        for job_name, job_config in workflow["jobs"].items():
            if not isinstance(job_config, dict):
                print(f"ERROR: {file_path} - Job '{job_name}' must be a dictionary")
                return False

            if "runs-on" not in job_config:
                print(f"ERROR: {file_path} - Job '{job_name}' missing 'runs-on'")
                return False

        print(f"SUCCESS: {file_path} - Valid workflow structure")
        return True

    except Exception as e:
        print(f"ERROR: {file_path} - Structure validation error: {e}")
        return False


def validate_all_workflows() -> bool:
    """Validate all GitHub Actions workflows"""
    workflows_dir = Path(".github/workflows")

    if not workflows_dir.exists():
        print("ERROR: .github/workflows directory not found")
        return False

    workflow_files = list(workflows_dir.glob("*.yml")) + list(
        workflows_dir.glob("*.yaml")
    )

    if not workflow_files:
        print("ERROR: No workflow files found in .github/workflows")
        return False

    print(f"Found {len(workflow_files)} workflow files")
    print("=" * 50)

    all_valid = True

    for workflow_file in workflow_files:
        print(f"\nValidating {workflow_file.name}")
        print("-" * 30)

        # Validate YAML syntax
        if not validate_yaml_file(str(workflow_file)):
            all_valid = False
            continue

        # Validate workflow structure
        if not validate_workflow_structure(str(workflow_file)):
            all_valid = False

    return all_valid


def main():
    """Main function"""
    print("GitHub Actions Workflow Validator")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path(".github/workflows").exists():
        print("ERROR: Please run this script from the project root directory")
        sys.exit(1)

    # Validate all workflows
    success = validate_all_workflows()

    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: All workflows are valid!")
        print("\nNext steps:")
        print("1. Push to GitHub to trigger workflows")
        print("2. Monitor Actions tab for execution")
        print("3. Check for any runtime errors")
    else:
        print("ERROR: Some workflows have issues. Please fix them before pushing.")
        sys.exit(1)


if __name__ == "__main__":
    main()
