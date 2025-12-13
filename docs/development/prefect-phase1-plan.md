# Phase 1: Foundation Setup - Implementation Plan

## Decisions Made

- **Scope**: Minimal configuration only
- **Settings**: Essential fields only (not all 11)
- **Testing**: Simple test to verify config works
- **Structure**: Create subdirectories when needed (not now)

---

## Phase 1 Deliverables

### Files to Create

1. **`src/shared/prefect/__init__.py`**
   - Empty or minimal exports

2. **`src/shared/prefect/config.py`**
   - Minimal PrefectConfig class
   - Just basic getters for API URL and DB connection

### Files to Modify

1. **`src/config/settings.py`**
   - Add 3 essential Prefect fields:
     - `prefect_api_url`
     - `prefect_db_connection_url`
     - `prefect_work_pool_data_ingestion` (default work pool name)

2. **`deployment/env.example`**
   - Add Prefect configuration section with essential variables

### Testing

1. **Simple test** to verify:
   - PrefectConfig can be imported
   - Settings can be read
   - Config methods return expected values

---

## Implementation Details

### 1. Essential Settings Fields

**Add to `src/config/settings.py`:**

```python
# Prefect Configuration (Essential)
prefect_api_url: str = Field(
    default="http://localhost:4200/api",
    alias="PREFECT_API_URL"
)

prefect_db_connection_url: str = Field(
    default="postgresql+asyncpg://postgres:password@localhost:5432/prefect",
    alias="PREFECT_API_DATABASE_CONNECTION_URL"
)

prefect_work_pool_data_ingestion: str = Field(
    default="data-ingestion-pool",
    alias="PREFECT_WORK_POOL_DATA_INGESTION"
)
```

### 2. Minimal Config Module

**Create `src/shared/prefect/config.py`:**

```python
"""
Prefect Configuration Module (Minimal)

Provides basic Prefect configuration access.
"""
from src.config.settings import Settings

settings = Settings()


class PrefectConfig:
    """Minimal Prefect configuration management"""
    
    @staticmethod
    def get_api_url() -> str:
        """Get Prefect API URL"""
        return settings.prefect_api_url
    
    @staticmethod
    def get_db_connection_url() -> str:
        """Get Prefect database connection URL"""
        return settings.prefect_db_connection_url
    
    @staticmethod
    def get_work_pool_name() -> str:
        """Get default work pool name for data ingestion"""
        return settings.prefect_work_pool_data_ingestion
```

### 3. Environment Variables

**Add to `deployment/env.example`:**

```bash
# ============================================
# Prefect Configuration (Essential)
# ============================================
PREFECT_API_URL=http://localhost:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect
PREFECT_WORK_POOL_DATA_INGESTION=data-ingestion-pool
```

### 4. Simple Test

**Create `tests/unit/test_prefect_config.py`:**

```python
"""
Simple test for Prefect configuration
"""
import pytest
from src.shared.prefect.config import PrefectConfig


def test_prefect_config_import():
    """Test that PrefectConfig can be imported"""
    assert PrefectConfig is not None


def test_prefect_config_get_api_url():
    """Test getting API URL from config"""
    api_url = PrefectConfig.get_api_url()
    assert api_url is not None
    assert isinstance(api_url, str)
    assert api_url.startswith("http")


def test_prefect_config_get_db_connection_url():
    """Test getting database connection URL"""
    db_url = PrefectConfig.get_db_connection_url()
    assert db_url is not None
    assert isinstance(db_url, str)
    assert "postgresql+asyncpg://" in db_url


def test_prefect_config_get_work_pool_name():
    """Test getting work pool name"""
    pool_name = PrefectConfig.get_work_pool_name()
    assert pool_name is not None
    assert isinstance(pool_name, str)
```

---

## Phase 1 Checklist

- [ ] Create `src/shared/prefect/__init__.py`
- [ ] Create `src/shared/prefect/config.py` (minimal version)
- [ ] Update `src/config/settings.py` (add 3 essential Prefect fields)
- [ ] Update `deployment/env.example` (add Prefect section)
- [ ] Create `tests/unit/test_prefect_config.py` (simple tests)
- [ ] Run tests to verify everything works
- [ ] Verify Prefect database exists (manual check)
- [ ] Document Phase 1 completion

---

## What We're NOT Doing in Phase 1

- ❌ Full 11-field settings (only 3 essentials)
- ❌ Validation logic in config
- ❌ Helper utilities (`utils/helpers.py`)
- ❌ Work pool name resolution for multiple pools
- ❌ Complex error handling
- ❌ Database verification scripts
- ❌ Creating subdirectories (`flows/`, `tasks/`, etc.)

---

## Success Criteria

Phase 1 is complete when:

1. ✅ PrefectConfig can be imported
2. ✅ Settings can be read from environment/config
3. ✅ Simple tests pass
4. ✅ Configuration is documented in env.example
5. ✅ Ready to add first flow in Phase 2

---

## Next Steps After Phase 1

Once Phase 1 is complete, we'll move to Phase 2:
- Create first flow file (`polygon_flows.py`)
- Create tasks file (`data_ingestion_tasks.py`)
- Implement one simple flow
- Test the flow works

---

This minimal approach gets us started quickly and we can expand as needed.

