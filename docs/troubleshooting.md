# Troubleshooting Guide

This comprehensive guide covers common issues, solutions, and frequently asked questions for the Trading System.

## System Status

**Production-Ready Trading System** with comprehensive data integration and robust testing infrastructure.

## Frequently Asked Questions

### Installation Issues

**Q: What are the system requirements?**
A: The system requires:
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Windows 10+ (for local deployment)

**Q: How do I install the system?**
A: Follow these steps:
1. Clone the repository: `git clone https://github.com/nishantnayar/trading-system.git`
2. Create conda environment: `conda create -n trading-system python=3.11`
3. Install dependencies: `pip install -r requirements.txt`
4. Set up databases: `python scripts/setup_databases.py`
5. Configure environment: Copy `deployment/env.example` to `.env`

**Q: What if I get import errors?**
A: Ensure you're in the project root directory and have activated your conda environment. Check that all dependencies are installed with `pip list`.

### Configuration Problems

**Q: How do I configure the database?**
A: Edit your `.env` file with the correct database credentials:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
TRADING_DB_NAME=trading_system
PREFECT_DB_NAME=prefect
```

**Q: How do I get Alpaca API keys?**
A: 
1. Sign up at [Alpaca Markets](https://alpaca.markets/)
2. Go to your dashboard
3. Generate API keys
4. Add them to your `.env` file:
```env
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### Runtime Errors

**Q: The system won't start, what should I check?**
A: Check these in order:
1. Database connectivity: `python scripts/test_database_connections.py`
2. Environment variables: `cat .env`
3. Service logs: `tail -f logs/trading.log`
4. Port availability: Ensure ports 8001, 8501, 4200, 5432, 6379 are free

**Q: How do I check if all services are running?**
A: Use the health check script:
```bash
python scripts/run_tests.py check
```

**Q: How do I access the Streamlit UI?**
A: The Streamlit UI is available at `http://localhost:8501`. If it's not running, start it with:
```bash
python streamlit_ui/run_streamlit.py
```

## Common Issues

### Streamlit UI Issues

**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solution**: Install Streamlit and dependencies:
```bash
pip install streamlit plotly
```

**Error**: `Port 8501 is already in use`

**Solution**: Either stop the existing Streamlit process or use a different port:
```bash
# Kill existing process
pkill -f streamlit

# Or use different port
streamlit run streamlit_ui/streamlit_app.py --server.port 8502
```

**Error**: `Session state not persisting across pages`

**Solution**: Ensure session state is properly initialized in the main app:
```python
# In streamlit_app.py
def initialize_session_state():
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = 'AAPL'
```

**Error**: `Charts not displaying properly`

**Solution**: Check Plotly installation and data format:
```bash
pip install plotly
# Ensure data is in correct format for Plotly charts
```

### Database Connection Issues

**Error**: `Database connection error: connection to server at "localhost" (::1), port 5432 failed`

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

**Error**: `FATAL: database "trading_system" does not exist`

**Solution**: Run the database setup script:
```bash
python scripts/setup_databases.py
```

### API Errors

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure you're running from the project root directory:
```bash
cd /path/to/trading-system
python scripts/test_database_connections.py
```

**Error**: `pytest.mark.unit is not a registered marker`

**Solution**: Ensure `pytest.ini` exists with markers defined:
```ini
[tool:pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    database: Database tests
    slow: Slow tests
```

### Performance Problems

**Issue**: Slow database queries

**Solutions**:
1. Check database indexes
2. Monitor connection pool usage
3. Review query performance logs
4. Consider database optimization

**Issue**: High memory usage

**Solutions**:
1. Check for memory leaks in logs
2. Monitor service resource usage
3. Review data processing efficiency
4. Consider data archiving

## Database Issues

### Connection Problems

**Error**: `psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed`

**Troubleshooting Steps**:
1. Verify PostgreSQL is running
2. Check port 5432 is not blocked
3. Verify user credentials
4. Check firewall settings

### Schema Issues

**Error**: `Schema 'data_ingestion' for service 'data_ingestion' not found`

**Solution**: Run the database setup script:
```bash
python scripts/setup_databases.py
```

### Data Issues

**Error**: `Data validation failed`

**Solutions**:
1. Check data format and types
2. Verify required fields are present
3. Review data validation rules
4. Check for data corruption

## CI/CD Issues

### Workflow Failures

**Error**: `This request has been automatically failed because it uses a deprecated version of actions/upload-artifact: v3`

**Solution**: Update to latest action versions:
```yaml
# ❌ Old (deprecated)
- uses: actions/upload-artifact@v3

# ✅ New (current)
- uses: actions/upload-artifact@v4
```

**Error**: `Permission denied (publickey)`

**Solutions**:
1. Check repository permissions
2. Verify workflow permissions
3. Use built-in GITHUB_TOKEN
4. Check GitHub Pages source setting

### Build Failures

**Error**: `No coverage data found`

**Solution**: Ensure coverage is generated:
```bash
# Run tests with coverage
python scripts/run_tests.py all

# Check if coverage.xml exists
ls -la coverage.xml
```

**Error**: `Black formatting check failed`

**Solution**: Format code with Black:
```bash
black .
```

## Performance Issues

### Slow Startup

**Causes**:
- Database connection delays
- Large dependency loading
- Resource constraints

**Solutions**:
1. Check database connectivity
2. Monitor system resources
3. Review startup logs
4. Optimize imports

### Memory Issues

**Causes**:
- Memory leaks
- Large data processing
- Inefficient data structures

**Solutions**:
1. Monitor memory usage
2. Review data processing logic
3. Implement data streaming
4. Use memory profiling tools

### Database Performance

**Causes**:
- Missing indexes
- Inefficient queries
- Connection pool issues

**Solutions**:
1. Add database indexes
2. Optimize queries
3. Tune connection pool
4. Monitor query performance

## Getting Help

### Self-Help Resources

1. **Check Logs**: Review service logs for error details
2. **Run Diagnostics**: Use built-in diagnostic scripts
3. **Review Documentation**: Check relevant documentation sections
4. **Search Issues**: Look for similar issues in GitHub issues

### Diagnostic Commands

```bash
# Check system health
python scripts/run_tests.py check

# Test database connections
python scripts/test_database_connections.py

# Run full test suite
python scripts/run_tests.py all

# Check code quality
black --check .
isort --check-only .
flake8 .
mypy src/
```

### Support Channels

1. **GitHub Issues**: Create an issue for bugs or feature requests
2. **Discussions**: Use GitHub Discussions for questions
3. **Documentation**: Check the comprehensive documentation
4. **Email**: Contact nishant.nayar@hotmail.com for urgent issues

### Reporting Issues

When reporting issues, please include:
1. **Error Message**: Complete error message and stack trace
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Environment**: Python version, OS, database version
4. **Logs**: Relevant log files and output
5. **Configuration**: Your `.env` file (remove sensitive data)

### Emergency Procedures

**System Down**:
1. Check service status
2. Review error logs
3. Restart services in order
4. Verify database connectivity

**Data Issues**:
1. Check database integrity
2. Review recent changes
3. Restore from backup if needed
4. Contact support immediately

---

**Remember**: Always test changes in a development environment before applying to production!
