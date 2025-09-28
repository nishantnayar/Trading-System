# Testing Strategy for Trading System

## Overview

The trading system uses a **two-tier testing approach**:

1. **Quick Verification Scripts** - For troubleshooting and quick checks
2. **Comprehensive Test Suite** - For full testing and CI/CD

## Quick Verification Scripts

### `scripts/test_database_connections.py`
**Purpose**: Quick database connectivity verification
**When to use**:
- After database setup
- When troubleshooting connection issues
- Quick verification before development
- CI/CD pipeline health checks

**Usage**:
```bash
python scripts/test_database_connections.py
```

**What it tests**:
- Trading database connection
- Prefect database connection
- Service schema accessibility
- Connection pool configuration

## Comprehensive Test Suite

### `tests/unit/test_database_connections.py`
**Purpose**: Comprehensive unit testing with pytest
**When to use**:
- Full test suite execution
- Development testing
- Code coverage analysis
- Integration with CI/CD

**Usage**:
```bash
# Run unit tests
python scripts/run_tests.py unit

# Run all tests with coverage
python scripts/run_tests.py all

# Run specific test
python scripts/run_tests.py tests/unit/test_database_connections.py
```

**What it tests**:
- All database connection functionality
- Configuration validation
- Service schema access
- Connection pool behavior
- Error handling scenarios

## Test Categories

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Database connections, configuration, schemas
- **Execution**: Fast, no external dependencies
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.database`

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions
- **Scope**: Schema creation, database structure, data integrity
- **Execution**: Medium speed, requires database
- **Markers**: `@pytest.mark.integration`, `@pytest.mark.database`

### 3. End-to-End Tests (Future)
- **Purpose**: Test complete workflows
- **Scope**: Full trading system functionality
- **Execution**: Slow, requires full system
- **Markers**: `@pytest.mark.e2e`, `@pytest.mark.slow`

## Test Execution Commands

### Quick Verification
```bash
# Database connectivity
python scripts/test_database_connections.py

# Database setup
python scripts/setup_databases.py
```

### Comprehensive Testing
```bash
# Unit tests only
python scripts/run_tests.py unit

# Integration tests only
python scripts/run_tests.py integration

# Database-specific tests
python scripts/run_tests.py database

# All tests with coverage
python scripts/run_tests.py all

# Quick tests (excluding slow)
python scripts/run_tests.py quick

# Parallel execution
python scripts/run_tests.py parallel
```

### Direct Pytest
```bash
# Run specific test file
pytest tests/unit/test_database_connections.py -v

# Run with markers
pytest -m "unit and database" -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Test Data Management

### Fixtures (`tests/conftest.py`)
- **Database engines**: Reusable database connections
- **Sessions**: Database sessions for testing
- **Configuration**: Test-specific configuration
- **Cleanup**: Automatic test data cleanup

### Test Isolation
- Each test runs in isolation
- Database state is reset between tests
- No test dependencies on external services
- Parallel execution support

## Coverage and Quality

### Coverage Reporting
```bash
# Generate HTML coverage report
python scripts/run_tests.py all

# View coverage report
open htmlcov/index.html
```

### Code Quality
- **Linting**: Flake8, Black, isort
- **Type Checking**: mypy
- **Security**: bandit
- **Dependencies**: safety

## CI/CD Integration

### GitHub Actions (Future)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run quick verification
        run: python scripts/test_database_connections.py
      - name: Run unit tests
        run: python scripts/run_tests.py unit
      - name: Run integration tests
        run: python scripts/run_tests.py integration
```

## Best Practices

### 1. Test Naming
- Use descriptive test names
- Follow pattern: `test_<functionality>_<scenario>`
- Group related tests in classes

### 2. Test Organization
- One test file per module/component
- Separate unit and integration tests
- Use appropriate markers

### 3. Test Data
- Use fixtures for common setup
- Create test data in tests, not in fixtures
- Clean up after each test

### 4. Assertions
- Use specific assertions
- Test both success and failure cases
- Verify error messages and codes

### 5. Performance
- Keep unit tests fast (< 1 second)
- Mark slow tests appropriately
- Use parallel execution when possible

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database status
   python scripts/test_database_connections.py
   
   # Verify environment variables
   cat .env
   ```

2. **Tests Not Found**
   ```bash
   # Check test discovery
   pytest --collect-only
   
   # Run specific test
   pytest tests/unit/test_database_connections.py -v
   ```

3. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"
   
   # Verify src directory
   ls -la src/
   ```

### Debug Mode
```bash
# Run with debug output
pytest -v -s --tb=long

# Run single test with debug
pytest tests/unit/test_database_connections.py::TestDatabaseConnections::test_trading_database_connection -v -s
```

## Future Enhancements

### Phase 2: Schema Tests
- Table creation tests
- Constraint validation tests
- Index performance tests
- Partitioning tests

### Phase 3: Data Model Tests
- CRUD operation tests
- Transaction tests
- Concurrency tests
- Validation tests

### Phase 4: Integration Tests
- Service integration tests
- API integration tests
- Prefect workflow tests
- Redis integration tests

### Phase 5: Performance Tests
- Load testing
- Stress testing
- Benchmark testing
- Memory profiling

---

**Summary**: Keep both test approaches - they serve different purposes and complement each other in a comprehensive testing strategy.
