#!/usr/bin/env python3
"""
Trigger Documentation Deployment Script
Creates a small change to trigger the GitHub Pages deployment workflow.
"""

import os
import subprocess
from datetime import datetime


def trigger_docs_deployment():
    """Trigger the documentation deployment by making a small change"""
    print("Triggering Documentation Deployment...")
    print("=" * 50)
    
    # Create a small change to trigger the workflow
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update the README with a deployment timestamp
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Add a deployment trigger comment
        trigger_comment = f"\n<!-- Last deployment trigger: {timestamp} -->\n"
        
        if "Last deployment trigger:" not in content:
            with open(readme_path, 'a') as f:
                f.write(trigger_comment)
            print(f"SUCCESS: Added deployment trigger to README.md")
        else:
            # Update existing trigger
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "Last deployment trigger:" in line:
                    lines[i] = f"<!-- Last deployment trigger: {timestamp} -->"
                    break
            
            with open(readme_path, 'w') as f:
                f.write('\n'.join(lines))
            print(f"SUCCESS: Updated deployment trigger in README.md")
    
    # Check git status
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if result.stdout.strip():
            print("SUCCESS: Changes detected by git")
            print("Files changed:")
            print(result.stdout)
            
            # Add and commit changes
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Trigger docs deployment - {timestamp}"], check=True)
            print("SUCCESS: Changes committed")
            
            # Push to trigger workflow
            subprocess.run(["git", "push"], check=True)
            print("SUCCESS: Changes pushed to GitHub")
            print()
            print("The documentation workflow should now be triggered!")
            print("Check the Actions tab: https://github.com/nishantnayar/trading-system/actions")
            print("Your site will be available at: https://nishantnayar.github.io/trading-system")
            
        else:
            print("INFO: No changes detected - workflow may already be up to date")
            
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Git command failed: {e}")
        return False
    except FileNotFoundError:
        print("ERROR: Git not found - please run git commands manually")
        return False
    
    return True


def main():
    """Main function"""
    print("Documentation Deployment Trigger")
    print("=" * 50)
    
    success = trigger_docs_deployment()
    
    if success:
        print("\n" + "=" * 50)
        print("SUCCESS: Documentation deployment triggered!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("ERROR: Failed to trigger deployment")
        print("=" * 50)
    
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
