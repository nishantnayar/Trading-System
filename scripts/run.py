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


def run_sphinx():
    """Start the Sphinx documentation server."""
    print("Starting Sphinx server...")
    print("Documentation will be available at: http://127.0.0.1:8001")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Build Sphinx docs first
        sphinx_dir = Path("docs/sphinx")
        if not sphinx_dir.exists():
            print("Error: docs/sphinx/ directory not found")
            return False
            
        # Build Sphinx documentation
        print("Building Sphinx documentation...")
        subprocess.run(["sphinx-build", "-b", "html", ".", "_build/html"], 
                      cwd=sphinx_dir, check=True)
        
        # Start a simple HTTP server
        import http.server
        import socketserver
        import os
        
        os.chdir(sphinx_dir / "_build" / "html")
        with socketserver.TCPServer(("", 8001), http.server.SimpleHTTPRequestHandler) as httpd:
            print("Sphinx server running at http://127.0.0.1:8001")
            httpd.serve_forever()
            
    except subprocess.CalledProcessError as e:
        print(f"Error building Sphinx: {e}")
        return False
    except KeyboardInterrupt:
        print("\nSphinx server stopped")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Simple Trading System Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run.py mkdocs     # Start MkDocs server (http://127.0.0.1:8000)
  python scripts/run.py sphinx     # Start Sphinx server (http://127.0.0.1:8001)
        """
    )
    
    parser.add_argument("command", choices=["mkdocs", "sphinx"], 
                       help="Command to run")
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("Error: Please run this script from the trading-system root directory")
        sys.exit(1)
    
    # Run the requested command
    if args.command == "mkdocs":
        success = run_mkdocs()
    elif args.command == "sphinx":
        success = run_sphinx()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
