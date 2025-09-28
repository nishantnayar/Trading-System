# CI/CD Pipeline Troubleshooting Guide

## Common Issues and Solutions

### 1. **Deprecated Action Versions**

#### **Error**: `This request has been automatically failed because it uses a deprecated version of actions/upload-artifact: v3`

**Solution**: Update to latest action versions
```yaml
# ❌ Old (deprecated)
- uses: actions/upload-artifact@v3

# ✅ New (current)
- uses: actions/upload-artifact@v4
```

**Updated Actions**:
- `actions/upload-artifact@v4`
- `actions/setup-python@v5`
- `actions/cache@v4`
- `codecov/codecov-action@v4`
- `peaceiris/actions-gh-pages@v4`
- `github/codeql-action/upload-sarif@v3`

### 2. **Permission Errors**

#### **Error**: `PermissionError: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`

**Solution**: Use different ports
```bash
# ❌ Port in use
mkdocs serve --dev-addr=127.0.0.1:8001

# ✅ Alternative ports
mkdocs serve --dev-addr=127.0.0.1:8002
mkdocs serve --dev-addr=127.0.0.1:8003
```

### 3. **Database Connection Issues**

#### **Error**: `Database connection error: connection to server at "localhost" (::1), port 5432 failed`

**Solutions**:

1. **Check PostgreSQL Status**:
   ```bash
   # Windows
   net start postgresql-x64-15
   
   # Linux/macOS
   sudo systemctl start postgresql
   sudo service postgresql start
   ```

2. **Verify Database Exists**:
   ```bash
   python scripts/test_database_connections.py
   ```

3. **Check Environment Variables**:
   ```bash
   # Verify .env file exists and has correct values
   cat .env
   ```

### 4. **Test Failures**

#### **Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Update Python path in test scripts
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))
```

#### **Error**: `pytest.mark.unit is not a registered marker`

**Solution**: Ensure `pytest.ini` exists with markers defined
```ini
[tool:pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    database: Database tests
    slow: Slow tests
```

### 5. **Documentation Build Issues**

#### **Error**: `WARNING - Doc file 'index.md' contains a link 'getting-started/installation.md', but the target is not found`

**Solutions**:

1. **Create Missing Files**:
   ```bash
   mkdir -p docs/getting-started
   mkdir -p docs/user-guide
   mkdir -p docs/api
   mkdir -p docs/troubleshooting
   ```

2. **Remove Broken Links** (temporary):
   ```markdown
   <!-- Comment out broken links -->
   <!-- - [Installation Guide](getting-started/installation.md) -->
   ```

3. **Use Placeholder Files**:
   ```bash
   touch docs/getting-started/installation.md
   echo "# Installation Guide\n\nComing soon..." > docs/getting-started/installation.md
   ```

### 6. **Security Scan Failures**

#### **Error**: `bandit: No such file or directory`

**Solution**: Install security tools
```bash
pip install bandit safety semgrep
```

#### **Error**: `safety: command not found`

**Solution**: Install safety
```bash
pip install safety
```

### 7. **Coverage Report Issues**

#### **Error**: `No coverage data found`

**Solution**: Ensure coverage is generated
```bash
# Run tests with coverage
python scripts/run_tests.py all

# Check if coverage.xml exists
ls -la coverage.xml
```

### 8. **GitHub Pages Deployment Issues**

#### **Error**: `Permission denied (publickey)`

**Solution**: Check GitHub token permissions
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Ensure token has `repo` and `workflow` permissions
3. Update repository secrets if needed

### 9. **Workflow Syntax Errors**

#### **Error**: `YAML syntax error`

**Solutions**:

1. **Validate YAML**:
   ```bash
   # Install yamllint
   pip install yamllint
   
   # Check syntax
   yamllint .github/workflows/
   ```

2. **Use Online Validator**:
   - https://www.yamllint.com/
   - GitHub Actions editor

3. **Check Indentation**:
   - Use spaces, not tabs
   - Consistent indentation (2 spaces)

### 10. **Local Testing**

#### **Test Workflows Locally**:

1. **Install act**:
   ```bash
   # macOS
   brew install act
   
   # Windows (Chocolatey)
   choco install act
   
   # Linux
   curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   ```

2. **Test Specific Workflow**:
   ```bash
   # Dry run
   act -W .github/workflows/ci.yml --dry-run
   
   # Run specific job
   act -W .github/workflows/ci.yml -j code-quality
   ```

3. **Use Test Script**:
   ```bash
   python scripts/test_github_actions.py
   ```

## Debugging Commands

### **Check Workflow Status**
```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

### **Local Environment Check**
```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check database connection
python scripts/test_database_connections.py

# Run tests locally
python scripts/run_tests.py all
```

### **GitHub CLI Commands**
```bash
# Check workflow status
gh workflow list
gh workflow run ci.yml
gh workflow run cd.yml -f environment=staging

# View logs
gh run view --log
```

## Prevention Strategies

### **1. Pre-commit Hooks**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### **2. Local Validation**
```bash
# Test before pushing
python scripts/test_github_actions.py
python scripts/run_tests.py all
mkdocs build
```

### **3. Environment Consistency**
```bash
# Use same Python version
pyenv local 3.11

# Use same dependencies
pip install -r requirements-test.txt
```

### **4. Regular Updates**
```bash
# Update action versions monthly
# Check for deprecation warnings
# Update dependencies regularly
```

## Emergency Procedures

### **Skip CI (Emergency Only)**
```bash
git commit -m "Emergency fix [skip ci]"
```

### **Rollback Deployment**
```bash
# Trigger rollback workflow
gh workflow run rollback.yml
```

### **Disable Workflows**
1. Go to repository Settings > Actions
2. Disable specific workflows temporarily
3. Re-enable after fixing issues

## Getting Help

### **GitHub Actions Documentation**
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Marketplace Actions](https://github.com/marketplace?type=actions)

### **Community Resources**
- [GitHub Community](https://github.community/c/github-actions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/github-actions)

### **Project Resources**
- [CI/CD Pipeline Docs](CI_CD_PIPELINE.md)
- [Testing Strategy](TESTING_STRATEGY.md)
- [Database Setup](DATABASE_SETUP.md)

---

**Remember**: Always test changes locally before pushing to avoid breaking the CI/CD pipeline!
