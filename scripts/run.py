#!/usr/bin/env python3
"""
Simple Trading System Runner

A basic script to run common development tasks.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_mkdocs():
    """Start MkDocs development server."""
    print("Starting MkDocs server...")
    print("Documentation will be available at: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Check if mkdocs.yml exists in the project root
        mkdocs_config = Path("mkdocs.yml")
        if not mkdocs_config.exists():
            print("Error: mkdocs.yml not found in project root")
            return False
            
        # Check if the docs directory exists
        docs_dir = Path("docs")
        if not docs_dir.exists():
            print("Error: docs/ directory not found")
            return False
            
        # Start MkDocs server with default config
        cmd = ["mkdocs", "serve"]
        subprocess.run(cmd, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error starting MkDocs: {e}")
        return False
    except KeyboardInterrupt:
        print("\nMkDocs server stopped")
        return True




def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Simple Trading System Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run.py mkdocs     # Start MkDocs server (http://127.0.0.1:8000)
        """
    )
    
    parser.add_argument("command", choices=["mkdocs"], 
                       help="Command to run")
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("Error: Please run this script from the trading-system root directory")
        sys.exit(1)
    
    # Run the requested command
    if args.command == "mkdocs":
        success = run_mkdocs()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
