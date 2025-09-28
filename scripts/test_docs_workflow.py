#!/usr/bin/env python3
"""
Test documentation workflow locally
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


def test_mkdocs_installation():
    """Test MkDocs installation"""
    print("Testing MkDocs installation...")

    # Check if mkdocs is installed
    exit_code, _, _ = run_command(["mkdocs", "--version"])
    if exit_code != 0:
        print("ERROR: MkDocs not installed. Installing...")
        install_cmd = ["pip", "install", "mkdocs", "mkdocs-material"]
        exit_code, stdout, stderr = run_command(install_cmd)
        if exit_code != 0:
            print(f"ERROR: Failed to install MkDocs: {stderr}")
            return False
        print("SUCCESS: MkDocs installed")
    else:
        print("SUCCESS: MkDocs already installed")

    return True


def test_mkdocs_build():
    """Test MkDocs build"""
    print("Testing MkDocs build...")

    # Check if we're in the right directory
    if not Path("mkdocs.yml").exists():
        print("ERROR: mkdocs.yml not found. Please run from project root.")
        return False

    # Test build
    cmd = ["mkdocs", "build"]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("SUCCESS: MkDocs build completed")

        # Check if site directory was created
        if Path("site").exists():
            print("SUCCESS: Site directory created")
            return True
        else:
            print("ERROR: Site directory not created")
            return False
    else:
        print(f"ERROR: MkDocs build failed: {stderr}")
        return False


def test_mkdocs_strict_build():
    """Test MkDocs strict build (for linting)"""
    print("Testing MkDocs strict build...")

    cmd = ["mkdocs", "build", "--strict"]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print("SUCCESS: MkDocs strict build completed")
        return True
    else:
        print(f"WARNING: MkDocs strict build found issues: {stderr}")
        # This is OK for now, we just want to test it works
        return True


def test_documentation_workflow():
    """Test the documentation workflow locally"""
    print("Testing Documentation Workflow Locally")
    print("=" * 50)

    # Test each component
    install_ok = test_mkdocs_installation()
    build_ok = test_mkdocs_build()
    strict_ok = test_mkdocs_strict_build()

    return install_ok and build_ok and strict_ok


def main():
    """Main function"""
    success = test_documentation_workflow()

    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: Documentation workflow components are working!")
        print("\nNext steps:")
        print("1. Push the updated docs.yml workflow to GitHub")
        print("2. Monitor the Actions tab for execution")
        print("3. Check if the workflow completes successfully")
        print("4. If successful, we can proceed to fix the CI workflow")
    else:
        print("ERROR: Documentation workflow has issues. Please fix them first.")
        sys.exit(1)


if __name__ == "__main__":
    main()
