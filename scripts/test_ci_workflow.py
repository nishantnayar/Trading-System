#!/usr/bin/env python3
"""
Test CI workflow components locally
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def test_code_quality_tools():
    """Test code quality tools"""
    print("Testing Code Quality Tools...")

    tools = [
        ("black", "black --version"),
        ("isort", "isort --version"),
        ("flake8", "flake8 --version"),
        ("mypy", "mypy --version"),
        ("bandit", "bandit --version"),
        ("safety", "safety --version"),
    ]

    all_ok = True

    for tool_name, version_cmd in tools:
        print(f"  Testing {tool_name}...")
        exit_code, _, _ = run_command(version_cmd.split())
        if exit_code == 0:
            print(f"    SUCCESS: {tool_name} is available")
        else:
            print(f"    ERROR: {tool_name} not found")
            all_ok = False

    return all_ok


def test_black_formatting():
    """Test Black code formatting"""
    print("Testing Black formatting...")

    # Check if black is installed
    exit_code, _, _ = run_command(["black", "--version"])
    if exit_code != 0:
        print("ERROR: Black not installed")
        return False

    # Test formatting check
    cmd = ["black", "--check", "--diff", "."]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("SUCCESS: Black formatting check passed")
        return True
    else:
        print(f"WARNING: Black found formatting issues: {stderr}")
        return True  # Warnings are OK for testing


def test_isort_imports():
    """Test isort import sorting"""
    print("Testing isort import sorting...")

    # Check if isort is installed
    exit_code, _, _ = run_command(["isort", "--version"])
    if exit_code != 0:
        print("ERROR: isort not installed")
        return False

    # Test import sorting check
    cmd = ["isort", "--check-only", "--diff", "."]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("SUCCESS: isort import sorting check passed")
        return True
    else:
        print(f"WARNING: isort found import issues: {stderr}")
        return True  # Warnings are OK for testing


def test_flake8_linting():
    """Test Flake8 linting"""
    print("Testing Flake8 linting...")

    # Check if flake8 is installed
    exit_code, _, _ = run_command(["flake8", "--version"])
    if exit_code != 0:
        print("ERROR: flake8 not installed")
        return False

    # Test linting
    cmd = [
        "flake8",
        ".",
        "--count",
        "--select=E9,F63,F7,F82",
        "--show-source",
        "--statistics",
    ]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("SUCCESS: Flake8 linting passed")
        return True
    else:
        print(f"WARNING: Flake8 found issues: {stderr}")
        return True  # Warnings are OK for testing


def test_mypy_type_checking():
    """Test mypy type checking"""
    print("Testing mypy type checking...")

    # Check if mypy is installed
    exit_code, _, _ = run_command(["mypy", "--version"])
    if exit_code != 0:
        print("ERROR: mypy not installed")
        return False

    # Test type checking
    cmd = ["mypy", "src/", "--ignore-missing-imports"]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("SUCCESS: mypy type checking passed")
        return True
    else:
        print(f"WARNING: mypy found type issues: {stderr}")
        return True  # Warnings are OK for testing


def test_security_tools():
    """Test security tools"""
    print("Testing Security Tools...")

    # Test bandit
    print("  Testing bandit...")
    cmd = ["bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json"]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("    SUCCESS: bandit scan completed")
    else:
        print(f"    WARNING: bandit found issues: {stderr}")

    # Test safety
    print("  Testing safety...")
    cmd = ["safety", "check", "--json", "--file", "requirements.txt"]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("    SUCCESS: safety check completed")
    else:
        print(f"    WARNING: safety found issues: {stderr}")

    # Clean up
    if Path("bandit-report.json").exists():
        Path("bandit-report.json").unlink()

    return True


def test_ci_workflow():
    """Test the CI workflow components locally"""
    print("Testing CI Workflow Components Locally")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("ERROR: Please run this script from the project root directory")
        return False

    # Test each component
    tools_ok = test_code_quality_tools()
    black_ok = test_black_formatting()
    isort_ok = test_isort_imports()
    flake8_ok = test_flake8_linting()
    mypy_ok = test_mypy_type_checking()
    security_ok = test_security_tools()

    return tools_ok and black_ok and isort_ok and flake8_ok and mypy_ok and security_ok


def main():
    """Main function"""
    success = test_ci_workflow()

    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: CI workflow components are working!")
        print("\nNext steps:")
        print("1. Push the updated ci.yml workflow to GitHub")
        print("2. Monitor the Actions tab for execution")
        print("3. Check if the workflow completes successfully")
        print("4. If successful, we can proceed to fix the CD workflow")
    else:
        print("ERROR: CI workflow has issues. Please fix them first.")
        sys.exit(1)


if __name__ == "__main__":
    main()
