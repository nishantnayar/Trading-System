#!/usr/bin/env python3
"""
Quick fix script for GitHub Pages deployment issues
"""

import os
import sys
from pathlib import Path


def check_repository_settings():
    """Check if repository is properly configured for GitHub Pages"""
    print("GitHub Pages Configuration Checker")
    print("=" * 50)

    print("\n1. Repository Settings Check:")
    print("   Go to: https://github.com/nishantnayar/trading-system/settings/pages")
    print("   Ensure:")
    print("   - Source: GitHub Actions")
    print("   - Status: Enabled")

    print("\n2. Workflow Permissions Check:")
    print("   Go to: https://github.com/nishantnayar/trading-system/settings/actions")
    print("   Ensure:")
    print("   - Workflow permissions: Read and write permissions")
    print("   - Allow GitHub Actions to create and approve pull requests: Checked")

    print("\n3. Actions Workflow Check:")
    print("   Go to: https://github.com/nishantnayar/trading-system/actions")
    print("   Look for 'Documentation' workflow")
    print("   Check if it completed successfully")


def create_manual_deployment():
    """Create instructions for manual deployment"""
    print("\nManual Deployment Instructions:")
    print("=" * 50)

    print("\nIf automatic deployment fails, you can deploy manually:")
    print("\n1. Build documentation locally:")
    print("   mkdocs build")

    print("\n2. Create gh-pages branch:")
    print("   git checkout --orphan gh-pages")
    print("   git rm -rf .")
    print("   cp -r site/* .")
    print("   git add .")
    print("   git commit -m 'Deploy documentation'")
    print("   git push origin gh-pages")

    print("\n3. Set Pages source to 'Deploy from a branch':")
    print("   - Go to repository Settings > Pages")
    print("   - Source: Deploy from a branch")
    print("   - Branch: gh-pages")
    print("   - Folder: / (root)")


def check_workflow_file():
    """Check if workflow file has correct permissions"""
    workflow_file = Path(".github/workflows/docs.yml")

    if not workflow_file.exists():
        print("ERROR: Workflow file not found")
        return False

    print("\nWorkflow File Check:")
    print("=" * 30)

    with open(workflow_file, "r") as f:
        content = f.read()

    # Check for permissions
    if "permissions:" in content:
        print("SUCCESS: Permissions section found")
    else:
        print("ERROR: Permissions section missing")
        return False

    # Check for modern actions
    if "actions/configure-pages@v4" in content:
        print("SUCCESS: Modern GitHub Pages actions found")
    else:
        print("ERROR: Using deprecated actions")
        return False

    # Check for proper job structure
    if "actions/deploy-pages@v4" in content:
        print("SUCCESS: Deploy action found")
    else:
        print("ERROR: Deploy action missing")
        return False

    return True


def main():
    """Main function"""
    print("GitHub Pages Fix Script")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path(".github/workflows").exists():
        print("ERROR: Please run this script from the project root directory")
        sys.exit(1)

    # Check workflow file
    if not check_workflow_file():
        print("\nERROR: Workflow file needs updates")
        print("Run: git add . && git commit -m 'Fix GitHub Pages workflow' && git push")
        sys.exit(1)

    # Provide instructions
    check_repository_settings()
    create_manual_deployment()

    print("\n" + "=" * 50)
    print("Next Steps:")
    print("1. Follow the repository settings instructions above")
    print("2. Push your changes to trigger the workflow")
    print("3. Monitor the Actions tab for deployment status")
    print("4. If it still fails, use manual deployment method")

    print("\nGitHub Pages URL:")
    print("https://nishantnayar.github.io/trading-system")


if __name__ == "__main__":
    main()
