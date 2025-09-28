#!/usr/bin/env python3
"""
Test GitHub Actions workflows locally using act or manual testing
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

def run_command(cmd: List[str], cwd: str = None) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_act_installed() -> bool:
    """Check if act is installed for local GitHub Actions testing"""
    exit_code, _, _ = run_command(["act", "--version"])
    return exit_code == 0

def test_workflow_locally(workflow_file: str) -> bool:
    """Test a GitHub Actions workflow locally using act"""
    if not check_act_installed():
        print("ERROR: 'act' is not installed. Install it from: https://github.com/nektos/act")
        print("   Or use: brew install act (macOS) / choco install act (Windows)")
        return False
    
    print(f"Testing workflow: {workflow_file}")
    
    # Test the workflow
    cmd = ["act", "-W", workflow_file, "--dry-run"]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code == 0:
        print(f"SUCCESS: Workflow {workflow_file} syntax is valid")
        return True
    else:
        print(f"ERROR: Workflow {workflow_file} has issues:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False

def test_workflow_syntax(workflow_file: str) -> bool:
    """Test workflow syntax using yamllint if available"""
    if not os.path.exists(workflow_file):
        print(f"ERROR: Workflow file not found: {workflow_file}")
        return False
    
    # Check if yamllint is available
    exit_code, _, _ = run_command(["yamllint", "--version"])
    if exit_code != 0:
        print("WARNING: yamllint not available, skipping YAML syntax check")
        return True
    
    print(f"Checking YAML syntax for: {workflow_file}")
    cmd = ["yamllint", workflow_file]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code == 0:
        print(f"SUCCESS: YAML syntax is valid for {workflow_file}")
        return True
    else:
        print(f"ERROR: YAML syntax issues in {workflow_file}:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False

def test_all_workflows() -> bool:
    """Test all GitHub Actions workflows"""
    workflows_dir = Path(".github/workflows")
    
    if not workflows_dir.exists():
        print("ERROR: .github/workflows directory not found")
        return False
    
    workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    
    if not workflow_files:
        print("ERROR: No workflow files found in .github/workflows")
        return False
    
    print(f"Found {len(workflow_files)} workflow files")
    
    all_valid = True
    
    for workflow_file in workflow_files:
        print(f"\nTesting {workflow_file.name}")
        print("=" * 50)
        
        # Test YAML syntax
        if not test_workflow_syntax(str(workflow_file)):
            all_valid = False
            continue
        
        # Test workflow with act (if available)
        if not test_workflow_locally(str(workflow_file)):
            all_valid = False
    
    return all_valid

def main():
    """Main function"""
    print("GitHub Actions Workflow Tester")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path(".github/workflows").exists():
        print("ERROR: Please run this script from the project root directory")
        sys.exit(1)
    
    # Test all workflows
    success = test_all_workflows()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: All workflows are valid!")
        print("\nTo run workflows locally:")
        print("   1. Install act: https://github.com/nektos/act")
        print("   2. Run: act -W .github/workflows/ci.yml")
        print("   3. Or test specific job: act -W .github/workflows/ci.yml -j code-quality")
    else:
        print("ERROR: Some workflows have issues. Please fix them before pushing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
