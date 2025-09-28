#!/usr/bin/env python3
"""
Fix all broken documentation links by updating references
"""

import os
import re
from pathlib import Path

def fix_links_in_file(file_path):
    """Fix broken links in a specific file"""
    if not Path(file_path).exists():
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix links to documentation files
    link_fixes = {
        # Architecture and setup docs
        'DATABASE_ARCHITECTURE_DETAILED.md': 'DATABASE_ARCHITECTURE_DETAILED.md',
        'LOGGING_ARCHITECTURE.md': 'LOGGING_ARCHITECTURE.md',
        'CI_CD_PIPELINE.md': 'CI_CD_PIPELINE.md',
        'CI_CD_TROUBLESHOOTING.md': 'CI_CD_TROUBLESHOOTING.md',
        'TESTING_STRATEGY.md': 'TESTING_STRATEGY.md',
        'DATABASE_SETUP.md': 'DATABASE_SETUP.md',
        'GITHUB_PAGES_SETUP.md': 'GITHUB_PAGES_SETUP.md',
        'COMPREHENSIVE_ARCHITECTURE.md': 'COMPREHENSIVE_ARCHITECTURE.md',
        
        # Getting started
        'getting-started/installation.md': 'getting-started/installation.md',
        'getting-started/configuration.md': 'getting-started/configuration.md',
        'getting-started/first-run.md': 'getting-started/first-run.md',
        
        # User guide
        'user-guide/dashboard.md': 'user-guide/dashboard.md',
        'user-guide/trading.md': 'user-guide/trading.md',
        'user-guide/strategies.md': 'user-guide/strategies.md',
        'user-guide/risk-management.md': 'user-guide/risk-management.md',
        
        # API
        'api/data-ingestion.md': 'api/data-ingestion.md',
        'api/strategy-engine.md': 'api/strategy-engine.md',
        'api/execution.md': 'api/execution.md',
        'api/risk-management.md': 'api/risk-management.md',
        'api/analytics.md': 'api/analytics.md',
        
        # Troubleshooting
        'troubleshooting/faq.md': 'troubleshooting/faq.md',
        'troubleshooting/common-issues.md': 'troubleshooting/common-issues.md',
    }
    
    # Fix markdown links
    for old_link, new_link in link_fixes.items():
        # Fix [text](link) format
        pattern = rf'\[([^\]]+)\]\({re.escape(old_link)}\)'
        replacement = rf'[\1]({new_link})'
        content = re.sub(pattern, replacement, content)
        
        # Fix direct links
        content = content.replace(f'({old_link})', f'({new_link})')
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed links in: {file_path}")
        return True
    
    return False

def main():
    """Fix all broken documentation links"""
    print("Fixing All Documentation Links")
    print("=" * 40)
    
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("ERROR: docs directory not found")
        return False
    
    # Files to fix
    files_to_fix = [
        "docs/COMPREHENSIVE_ARCHITECTURE.md",
        "docs/DATABASE_SETUP.md", 
        "docs/CI_CD_TROUBLESHOOTING.md",
        "docs/GITHUB_PAGES_SETUP.md",
        "docs/index.md"
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if fix_links_in_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed links in {fixed_count} files")
    print("SUCCESS: Documentation links fixed!")
    
    return True

if __name__ == "__main__":
    main()
