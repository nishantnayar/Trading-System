#!/usr/bin/env python3
"""
Script to deploy MkDocs documentation to GitHub Pages
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Starting MkDocs deployment to GitHub Pages...")
    
    # Check if we're in the right directory
    if not Path("mkdocs.yml").exists():
        print("❌ Error: mkdocs.yml not found. Please run this script from the project root.")
        return False
    
    # Install MkDocs if not available
    print("📦 Installing MkDocs...")
    if not run_command("pip install mkdocs", "Installing MkDocs"):
        return False
    
    # Build documentation
    print("🔨 Building documentation...")
    if not run_command("mkdocs build", "Building MkDocs site"):
        return False
    
    # Check if site directory exists
    if not Path("site").exists():
        print("❌ Error: site directory not found after build")
        return False
    
    print("✅ Documentation built successfully!")
    print("📁 Site files are in the 'site' directory")
    print("🌐 You can now:")
    print("   1. Go to your GitHub repository settings")
    print("   2. Enable GitHub Pages")
    print("   3. Set source to 'GitHub Actions'")
    print("   4. The workflow will automatically deploy your docs")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
