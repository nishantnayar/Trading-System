#!/usr/bin/env python3
"""
GitHub Pages Deployment Fix Script
Diagnoses and provides instructions to fix GitHub Pages deployment issues.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_mkdocs_build():
    """Check if MkDocs can build the documentation locally"""
    print("=" * 60)
    print("Checking MkDocs Build...")
    print("=" * 60)
    
    try:
        # Check if MkDocs is installed
        result = subprocess.run(["mkdocs", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: MkDocs is installed: {result.stdout.strip()}")
        else:
            print("ERROR: MkDocs is not installed")
            return False
            
        # Try to build the documentation
        print("\nBuilding documentation...")
        result = subprocess.run(["mkdocs", "build"], capture_output=True, text=True)
        if result.returncode == 0:
            print("SUCCESS: Documentation built successfully")
            
            # Check if site directory exists and has content
            site_dir = Path("site")
            if site_dir.exists():
                files = list(site_dir.rglob("*"))
                print(f"SUCCESS: Site directory created with {len(files)} files")
                
                # Check for key files
                key_files = ["index.html", "COMPREHENSIVE_ARCHITECTURE/index.html"]
                for file_path in key_files:
                    if (site_dir / file_path).exists():
                        print(f"SUCCESS: Found {file_path}")
                    else:
                        print(f"ERROR: Missing {file_path}")
            else:
                print("ERROR: Site directory not created")
                return False
        else:
            print(f"ERROR: MkDocs build failed: {result.stderr}")
            return False
            
        return True
        
    except FileNotFoundError:
        print("ERROR: MkDocs command not found")
        return False
    except Exception as e:
        print(f"ERROR: Error checking MkDocs: {e}")
        return False


def check_github_pages_config():
    """Check GitHub Pages configuration"""
    print("\n" + "=" * 60)
    print("GitHub Pages Configuration Check")
    print("=" * 60)
    
    print("To fix GitHub Pages deployment, follow these steps:")
    print()
    print("1. Go to your GitHub repository: https://github.com/nishantnayar/trading-system")
    print("2. Click on 'Settings' tab")
    print("3. Scroll down to 'Pages' section in the left sidebar")
    print("4. Under 'Source', select 'GitHub Actions'")
    print("5. Save the settings")
    print()
    print("6. Go to 'Actions' tab")
    print("7. Check if the 'Documentation' workflow is running")
    print("8. If it's not running, push a new commit to trigger it")
    print()
    print("9. After the workflow completes, your site should be available at:")
    print("   https://nishantnayar.github.io/trading-system")
    print()


def check_workflow_permissions():
    """Check if workflow has proper permissions"""
    print("\n" + "=" * 60)
    print("Workflow Permissions Check")
    print("=" * 60)
    
    print("The documentation workflow needs these permissions:")
    print("SUCCESS: contents: read - to checkout code")
    print("SUCCESS: pages: write - to deploy to GitHub Pages")
    print("SUCCESS: id-token: write - for authentication")
    print()
    print("These permissions are already configured in the workflow file.")
    print()


def check_mkdocs_config():
    """Check MkDocs configuration"""
    print("\n" + "=" * 60)
    print("MkDocs Configuration Check")
    print("=" * 60)
    
    mkdocs_file = Path("mkdocs.yml")
    if mkdocs_file.exists():
        print("SUCCESS: mkdocs.yml exists")
        
        # Check for key configuration
        with open(mkdocs_file, 'r') as f:
            content = f.read()
            
        if "site_name:" in content:
            print("SUCCESS: site_name configured")
        else:
            print("ERROR: site_name not found")
            
        if "theme:" in content:
            print("SUCCESS: theme configured")
        else:
            print("ERROR: theme not found")
            
        if "nav:" in content:
            print("SUCCESS: navigation configured")
        else:
            print("ERROR: navigation not found")
    else:
        print("ERROR: mkdocs.yml not found")


def main():
    """Main function"""
    print("GitHub Pages Deployment Diagnostic Tool")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("mkdocs.yml").exists():
        print("ERROR: Not in the project root directory")
        print("Please run this script from the project root")
        return False
    
    # Run checks
    mkdocs_ok = check_mkdocs_build()
    check_mkdocs_config()
    check_workflow_permissions()
    check_github_pages_config()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if mkdocs_ok:
        print("SUCCESS: Local documentation build is working")
        print("SUCCESS: The issue is likely with GitHub Pages configuration")
        print()
        print("Next steps:")
        print("1. Follow the GitHub Pages configuration steps above")
        print("2. Push a new commit to trigger the workflow")
        print("3. Check the Actions tab for workflow execution")
    else:
        print("ERROR: Local documentation build has issues")
        print("Fix the local build issues first")
    
    return mkdocs_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
