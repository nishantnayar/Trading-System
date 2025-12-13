# Market Data Sources Integration

Comprehensive guide for integrating and managing multiple market data sources in the trading system.

## Table of Contents

- [Overview](#overview)
- [Multi-Source Architecture](#multi-source-architecture)
- [Polygon.io Integration](#polygonio-integration)
- [Yahoo Finance Integration](#yahoo-finance-integration)
- [Data Source Comparison](#data-source-comparison)
- [Database Schema](#database-schema)
- [Implementation Plan](#implementation-plan)
- [Best Practices](#best-practices)

---

## Overview

The trading system supports multiple market data sources to provide:

- **Redundancy**: Backup sources if one fails
- **Data Validation**: Cross-validate data between sources
- **Rich Data**: Different sources provide different data types
- **Cost Optimization**: Use free sources where possible
- **Flexibility**: Choose best source for each use case

### Supported Data Sources

| Source | OHLCV | Fundamentals | Dividends | Splits | Real-time | Cost |
|--------|-------|--------------|-----------|---------|-----------|------|
| **Polygon.io** | ✅ | ❌ | ✅ | ✅ | ✅ | Paid (Free tier: 5 calls/min) |
| **Yahoo Finance** | ✅ | ✅ | ✅ | ✅ | ⚠️ Delayed | Free (Unlimited) |
| **Alpaca** | ✅ | ❌ | ❌ | ❌ | ✅ | Free with account |

---

## Multi-Source Architecture

### Design Principles

1. **Independent Services**: Each data source has its own service module
2. **Unified Storage**: All market data stored in `data_ingestion.market_data` with `data_source` field
3. **Source Tracking**: Track which provider supplied each data point
4. **Separate Loaders**: Each source has dedicated loader class
5. **Consistent Interface**: Similar API patterns across sources

### Directory Structure

```
src/services/
├── polygon/
│   ├── __init__.py
│   ├── client.py           # PolygonClient
│   ├── exceptions.py       # Polygon-specific exceptions
│   └── models.py           # Pydantic models
│
├── yahoo/
│   ├── __init__.py
│   ├── client.py           # YahooClient
│   ├── exceptions.py       # Yahoo-specific exceptions
│   ├── models.py           # Pydantic models
│   └── loader.py           # YahooDataLoader
│
├── alpaca/
│   ├── __init__.py
│   ├── client.py           # AlpacaClient
│   └── exceptions.py
│
└── data_ingestion/
    ├── __init__.py
    ├── historical_loader.py  # HistoricalDataLoader (Polygon)
    └── symbols.py
```

### Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  Polygon.io │────▶│ PolygonClient│────▶│ HistoricalDataLoader│
└─────────────┘     └──────────────┘     └─────────────────────┘
                                                    │
                                                    │
┌─────────────┐     ┌──────────────┐     ┌─────────▼─────────┐
│Yahoo Finance│────▶│ YahooClient  │────▶│ YahooDataLoader   │
└─────────────┘     └──────────────┘     └───────────────────┘
                                                    │
                                                    │
┌─────────────┐     ┌──────────────┐               │
│   Alpaca    │────▶│ AlpacaClient │               │
└─────────────┘     └──────────────┘               │
                                                    │
                                         ┌──────────▼──────────┐
                                         │   PostgreSQL DB     │
                                         │  ┌──────────────┐   │
                                         │  │ market_data  │   │
                                         │  │ fundamentals │   │
                                         │  │ dividends    │   │
                                         │  │ splits       │   │
                                         │  └──────────────┘   │
                                         └─────────────────────┘
```

---

## Polygon.io Integration

### Overview

Polygon.io is the primary data source for high-quality, real-time market data. Ideal for production trading systems requiring accuracy and reliability.

### Features

- **Historical OHLCV**: Minute, hour, day, week, month aggregates
- **Real-time Data**: WebSocket streaming (paid plans)
- **Corporate Actions**: Dividends, splits
- **Adjusted Data**: Split-adjusted and dividend-adjusted prices
- **Tick Data**: Individual trades and quotes (paid plans)

### Configuration

```bash
# Environment variables
POLYGON_API_KEY=your_api_key_here
POLYGON_BASE_URL=https://api.polygon.io
```

### Usage

```python
from src.services.data_ingestion.historical_loader import HistoricalDataLoader

# Initialize loader for Polygon (default)
loader = HistoricalDataLoader(
    batch_size=100,
    requests_per_minute=2,  # Free tier limit
    data_source="polygon"
)

# Load data
await loader.load_symbol_data(
    symbol="AAPL",
    days_back=30,
    timespan="day"
)
```

### CLI

```bash
# Load Polygon data
python scripts/load_historical_data.py --symbol AAPL --days-back 30
```

### Rate Limits

- **Free Tier**: 5 requests/minute
- **Starter Plan**: 100 requests/minute
- **Developer Plan**: Unlimited

### Best Use Cases

- ✅ Production trading systems
- ✅ High-frequency data needs
- ✅ Real-time streaming
- ✅ Accurate corporate actions
- ❌ High-volume backtesting (expensive)
- ❌ Fundamental analysis (not available)

---

## Yahoo Finance Integration

### Overview

Yahoo Finance provides free, unlimited market data including OHLCV, fundamentals, dividends, and company information. Perfect for backtesting, fundamental analysis, and development.

### Implementation Status

**✅ Complete (10/10 data types implemented - 100%)**

All Yahoo Finance data types have been fully implemented:

| # | Data Type | Client Method | Loader Method | Database Model | SQL Script | CLI Flag | Status |
|---|-----------|---------------|---------------|----------------|------------|----------|--------|
| 1 | **Market Data (OHLCV)** | `get_historical_data()` | `load_market_data()` | `MarketData` | ✅ | `--market-data` | ✅ Complete |
| 2 | **Company Information** | `get_company_info()` | `load_company_info()` | `CompanyInfo` | ✅ | `--company-info` | ✅ Complete |
| 3 | **Key Statistics** | `get_key_statistics()` | `load_key_statistics()` | `KeyStatistics` | ✅ | `--key-statistics` | ✅ Complete |
| 4 | **Dividends** | `get_dividends()` | `load_dividends()` | `Dividend` | ✅ | `--dividends` | ✅ Complete |
| 5 | **Stock Splits** | `get_splits()` | `load_splits()` | `StockSplit` | ✅ | `--splits` | ✅ Complete |
| 6 | **Institutional Holders** | `get_institutional_holders()` | `load_institutional_holders()` | `InstitutionalHolder` | ✅ | `--institutional-holders` | ✅ Complete |
| 7 | **Financial Statements** | `get_financial_statements()` | `load_financial_statements()` | `FinancialStatement` | ✅ | `--financial-statements` | ✅ Complete |
| 8 | **Company Officers** | `get_company_officers()` | `load_company_officers()` | `CompanyOfficer` | ✅ | `--company-officers` | ✅ Complete |
| 9 | **Analyst Recommendations** | `get_analyst_recommendations()` | `load_analyst_recommendations()` | `AnalystRecommendation` | ✅ | `--analyst-recommendations` | ✅ Complete |
| 10 | **ESG Scores** | `get_esg_scores()` | `load_esg_scores()` | `ESGScore` | ✅ | `--esg-scores` | ✅ Complete |

**What's Working:**
- ✅ All core market data and fundamentals
- ✅ All financial statements and metrics
- ✅ Corporate actions (dividends, splits)
- ✅ Ownership data (institutional holders, officers)
- ✅ Analyst recommendations
- ✅ ESG scores
- ✅ Complete CLI integration
- ✅ Comprehensive test coverage

**Note:** HTTP 404 errors when loading ESG scores are expected and normal - not all symbols have ESG data available. These are handled silently by the system.

### Features

**Market Data:**
- ✅ Historical OHLCV (daily, hourly, minute)
- ✅ Adjusted close prices
- ✅ Volume data
- ✅ Intraday data (up to 60 days history)
- ⚠️ 15-minute delayed real-time data

**Fundamental Data:**
- ✅ Company profile (name, sector, industry, description)
- ✅ Key statistics (50+ metrics: market cap, PE ratios, profitability, financial health, growth, trading, ownership)
- ✅ Financial statements (income, balance sheet, cash flow)
- ✅ Earnings history and estimates
- ✅ Analyst recommendations
- ✅ Major shareholders

**Corporate Actions:**
- ✅ Dividends (amount, ex-date, payment date)
- ✅ Stock splits (ratio, date)

**Additional Data:**
- ✅ News and press releases
- ✅ Options chains (if needed)
- ✅ Institutional holdings

### Architecture

#### Components

```python
# Yahoo Client (src/services/yahoo/client.py)
class YahooClient:
    """Yahoo Finance API client using yfinance library"""
    
    async def get_historical_data(symbol, start_date, end_date, interval)
    async def get_company_info(symbol)
    async def get_financials(symbol)
    async def get_dividends(symbol, start_date, end_date)
    async def get_splits(symbol, start_date, end_date)
    async def get_key_statistics(symbol)
    async def health_check()

# Yahoo Loader (src/services/yahoo/loader.py)
class YahooDataLoader:
    """Load data from Yahoo Finance into database"""
    
    async def load_market_data(symbol, start_date, end_date)
    async def load_company_info(symbol)
    async def load_financials(symbol)
    async def load_dividends(symbol, start_date, end_date)
    async def load_splits(symbol, start_date, end_date)
    async def load_analyst_recommendations(symbol)
    async def load_esg_scores(symbol)
    async def load_all_data(symbol, start_date, end_date)
```

#### Pydantic Models

```python
# src/services/yahoo/models.py

class YahooBar(BaseModel):
    """OHLCV bar from Yahoo Finance"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: Optional[float]
    volume: int

class CompanyInfo(BaseModel):
    """Company profile and details"""
    symbol: str
    name: str
    sector: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    website: Optional[str]
    market_cap: Optional[int]
    employees: Optional[int]
    headquarters: Optional[str]

class KeyStatistics(BaseModel):
    """Key financial metrics"""
    symbol: str
    date: date
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    peg_ratio: Optional[float]
    price_to_book: Optional[float]
    price_to_sales: Optional[float]
    enterprise_value: Optional[int]
    profit_margin: Optional[float]
    operating_margin: Optional[float]
    return_on_assets: Optional[float]
    return_on_equity: Optional[float]
    revenue: Optional[int]
    revenue_per_share: Optional[float]
    earnings_per_share: Optional[float]
    dividend_yield: Optional[float]
    beta: Optional[float]
    fifty_two_week_high: Optional[float]
    fifty_two_week_low: Optional[float]

class Dividend(BaseModel):
    """Dividend payment"""
    symbol: str
    ex_date: date
    payment_date: Optional[date]
    amount: float
    data_source: str = "yahoo"

class StockSplit(BaseModel):
    """Stock split event"""
    symbol: str
    split_date: date
    ratio: str  # e.g., "2:1", "3:2"
    numerator: int
    denominator: int
    data_source: str = "yahoo"

class FinancialStatement(BaseModel):
    """Financial statement data"""
    symbol: str
    period_end: date
    statement_type: str  # 'income', 'balance_sheet', 'cash_flow'
    period_type: str  # 'annual', 'quarterly'
    data: dict  # Flexible JSON storage for all line items
```

### Database Schema

#### Existing Table Updates

```sql
-- market_data table already has data_source column (added in migration 07)
-- No changes needed - Yahoo data will use data_source='yahoo'

SELECT * FROM data_ingestion.market_data 
WHERE data_source = 'yahoo' AND symbol = 'AAPL';
```

#### New Tables Required

```sql
-- Company Information (basic profile - one row per company)
CREATE TABLE data_ingestion.company_info (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    description TEXT,
    website VARCHAR(255),
    phone VARCHAR(50),
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(100),
    employees INTEGER,
    market_cap BIGINT,
    currency VARCHAR(10),
    exchange VARCHAR(50),
    quote_type VARCHAR(50),
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    additional_data JSONB,  -- For flexible storage of remaining 150+ info fields
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE
);

-- Company Officers (one-to-many relationship)
CREATE TABLE data_ingestion.company_officers (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    age INTEGER,
    year_born INTEGER,
    fiscal_year INTEGER,
    total_pay BIGINT,
    exercised_value BIGINT,
    unexercised_value BIGINT,
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_name_fiscal UNIQUE (symbol, name, fiscal_year, data_source)
);

-- Key Statistics (time-series of financial metrics)
CREATE TABLE data_ingestion.key_statistics (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    
    -- Valuation Metrics
    market_cap BIGINT,
    enterprise_value BIGINT,
    trailing_pe DECIMAL(10,2),
    forward_pe DECIMAL(10,2),
    peg_ratio DECIMAL(10,2),
    price_to_book DECIMAL(10,2),
    price_to_sales DECIMAL(10,2),
    enterprise_to_revenue DECIMAL(10,2),
    enterprise_to_ebitda DECIMAL(10,2),
    
    -- Profitability Metrics
    profit_margin DECIMAL(10,4),
    operating_margin DECIMAL(10,4),
    return_on_assets DECIMAL(10,4),
    return_on_equity DECIMAL(10,4),
    gross_margin DECIMAL(10,4),
    ebitda_margin DECIMAL(10,4),
    
    -- Financial Health
    revenue BIGINT,
    revenue_per_share DECIMAL(15,4),
    earnings_per_share DECIMAL(15,4),
    total_cash BIGINT,
    total_debt BIGINT,
    debt_to_equity DECIMAL(10,2),
    current_ratio DECIMAL(10,4),
    quick_ratio DECIMAL(10,4),
    free_cash_flow BIGINT,
    operating_cash_flow BIGINT,
    
    -- Growth Metrics
    revenue_growth DECIMAL(10,4),
    earnings_growth DECIMAL(10,4),
    
    -- Trading Metrics
    beta DECIMAL(10,4),
    fifty_two_week_high DECIMAL(15,4),
    fifty_two_week_low DECIMAL(15,4),
    fifty_day_average DECIMAL(15,4),
    two_hundred_day_average DECIMAL(15,4),
    average_volume BIGINT,
    
    -- Dividend Metrics
    dividend_yield DECIMAL(10,4),
    dividend_rate DECIMAL(10,4),
    payout_ratio DECIMAL(10,4),
    
    -- Share Information
    shares_outstanding BIGINT,
    float_shares BIGINT,
    shares_short BIGINT,
    short_ratio DECIMAL(10,2),
    held_percent_insiders DECIMAL(10,4),
    held_percent_institutions DECIMAL(10,4),
    
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_date_source UNIQUE (symbol, date, data_source)
);

-- Institutional Holders (time-series - one-to-many)
CREATE TABLE data_ingestion.institutional_holders (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date_reported DATE NOT NULL,
    holder_name VARCHAR(255) NOT NULL,
    shares BIGINT,
    value BIGINT,
    percent_held DECIMAL(10,6),
    percent_change DECIMAL(10,6),
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_holder_date UNIQUE (symbol, holder_name, date_reported, data_source)
);

-- Analyst Recommendations (time-series)
CREATE TABLE data_ingestion.analyst_recommendations (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    period VARCHAR(10) NOT NULL,  -- '0m', '-1m', '-2m', '-3m'
    strong_buy INTEGER DEFAULT 0,
    buy INTEGER DEFAULT 0,
    hold INTEGER DEFAULT 0,
    sell INTEGER DEFAULT 0,
    strong_sell INTEGER DEFAULT 0,
    total_analysts INTEGER GENERATED ALWAYS AS (strong_buy + buy + hold + sell + strong_sell) STORED,
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_date_period UNIQUE (symbol, date, period, data_source)
);

-- Dividends (corporate action - already existed but refined)
CREATE TABLE data_ingestion.dividends (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    ex_date DATE NOT NULL,
    payment_date DATE,
    record_date DATE,
    amount DECIMAL(15,4) NOT NULL,
    dividend_type VARCHAR(20) DEFAULT 'regular',  -- 'regular', 'special', 'stock'
    currency VARCHAR(10) DEFAULT 'USD',
    data_source VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_exdate_source UNIQUE (symbol, ex_date, data_source),
    CONSTRAINT positive_dividend CHECK (amount > 0)
);

-- Stock Splits (corporate action - already existed but refined)
CREATE TABLE data_ingestion.stock_splits (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    split_date DATE NOT NULL,
    split_ratio DECIMAL(10,4) NOT NULL,  -- Numeric ratio (e.g., 2.0 for 2:1, 0.5 for 1:2)
    ratio_str VARCHAR(20),               -- Human readable (e.g., "2:1", "7:1")
    data_source VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_splitdate_source UNIQUE (symbol, split_date, data_source),
    CONSTRAINT positive_ratio CHECK (split_ratio > 0)
);

-- Financial Statements (JSONB for flexibility - 39-68 fields per statement)
CREATE TABLE data_ingestion.financial_statements (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    period_end DATE NOT NULL,
    statement_type VARCHAR(20) NOT NULL,  -- 'income', 'balance_sheet', 'cash_flow'
    period_type VARCHAR(20) NOT NULL,     -- 'annual', 'quarterly', 'ttm'
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    data JSONB NOT NULL,                  -- Full statement data (all line items)
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_period_statement UNIQUE (symbol, period_end, statement_type, period_type, data_source),
    CONSTRAINT valid_statement_type CHECK (statement_type IN ('income', 'balance_sheet', 'cash_flow')),
    CONSTRAINT valid_period_type CHECK (period_type IN ('annual', 'quarterly', 'ttm'))
);

-- Earnings Calendar (upcoming events and estimates)
CREATE TABLE data_ingestion.earnings_calendar (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    earnings_date DATE NOT NULL,
    earnings_call_date TIMESTAMP WITH TIME ZONE,
    eps_estimate_low DECIMAL(10,4),
    eps_estimate_high DECIMAL(10,4),
    eps_estimate_avg DECIMAL(10,4),
    revenue_estimate_low BIGINT,
    revenue_estimate_high BIGINT,
    revenue_estimate_avg BIGINT,
    is_estimate BOOLEAN DEFAULT true,
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_earnings_date UNIQUE (symbol, earnings_date, data_source)
);

-- ESG/Sustainability Scores
CREATE TABLE data_ingestion.esg_scores (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    total_esg DECIMAL(10,2),
    environment_score DECIMAL(10,2),
    social_score DECIMAL(10,2),
    governance_score DECIMAL(10,2),
    controversy_level INTEGER,
    esg_performance VARCHAR(20),  -- 'LAG_PERF', 'AVG_PERF', 'OUT_PERF'
    peer_group VARCHAR(100),
    peer_count INTEGER,
    percentile DECIMAL(10,2),
    data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_symbol FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE,
    CONSTRAINT unique_symbol_date_source UNIQUE (symbol, date, data_source)
);

-- Create indexes for performance
CREATE INDEX idx_company_info_sector ON data_ingestion.company_info(sector);
CREATE INDEX idx_company_info_industry ON data_ingestion.company_info(industry);
CREATE INDEX idx_company_info_country ON data_ingestion.company_info(country);

CREATE INDEX idx_company_officers_symbol ON data_ingestion.company_officers(symbol);
CREATE INDEX idx_company_officers_title ON data_ingestion.company_officers(title);
CREATE INDEX idx_company_officers_fiscal_year ON data_ingestion.company_officers(fiscal_year DESC);

CREATE INDEX idx_key_statistics_symbol_date ON data_ingestion.key_statistics(symbol, date DESC);
CREATE INDEX idx_key_statistics_market_cap ON data_ingestion.key_statistics(market_cap DESC NULLS LAST);
CREATE INDEX idx_key_statistics_pe_ratio ON data_ingestion.key_statistics(trailing_pe);

CREATE INDEX idx_institutional_holders_symbol_date ON data_ingestion.institutional_holders(symbol, date_reported DESC);
CREATE INDEX idx_institutional_holders_holder ON data_ingestion.institutional_holders(holder_name);
CREATE INDEX idx_institutional_holders_shares ON data_ingestion.institutional_holders(shares DESC);

CREATE INDEX idx_analyst_recommendations_symbol_date ON data_ingestion.analyst_recommendations(symbol, date DESC);

CREATE INDEX idx_dividends_symbol_date ON data_ingestion.dividends(symbol, ex_date DESC);
CREATE INDEX idx_dividends_ex_date ON data_ingestion.dividends(ex_date DESC);

CREATE INDEX idx_stock_splits_symbol_date ON data_ingestion.stock_splits(symbol, split_date DESC);
CREATE INDEX idx_stock_splits_split_date ON data_ingestion.stock_splits(split_date DESC);

CREATE INDEX idx_financial_statements_symbol ON data_ingestion.financial_statements(symbol, period_end DESC);
CREATE INDEX idx_financial_statements_type ON data_ingestion.financial_statements(statement_type, period_type);
CREATE INDEX idx_financial_statements_data ON data_ingestion.financial_statements USING gin(data);

CREATE INDEX idx_earnings_calendar_symbol ON data_ingestion.earnings_calendar(symbol);
CREATE INDEX idx_earnings_calendar_date ON data_ingestion.earnings_calendar(earnings_date DESC);

CREATE INDEX idx_esg_scores_symbol_date ON data_ingestion.esg_scores(symbol, date DESC);
CREATE INDEX idx_esg_scores_total ON data_ingestion.esg_scores(total_esg DESC NULLS LAST);

-- Add comments
COMMENT ON TABLE data_ingestion.company_info IS 'Company profile and basic information (one row per company)';
COMMENT ON TABLE data_ingestion.company_officers IS 'Company officers and executives (one-to-many, tracked by fiscal year)';
COMMENT ON TABLE data_ingestion.key_statistics IS 'Time-series of key financial metrics and ratios';
COMMENT ON TABLE data_ingestion.institutional_holders IS 'Institutional ownership history (time-series)';
COMMENT ON TABLE data_ingestion.analyst_recommendations IS 'Analyst recommendation counts over time';
COMMENT ON TABLE data_ingestion.dividends IS 'Dividend payment history from all sources';
COMMENT ON TABLE data_ingestion.stock_splits IS 'Stock split history from all sources';
COMMENT ON TABLE data_ingestion.financial_statements IS 'Financial statements stored as JSONB (income, balance sheet, cash flow)';
COMMENT ON TABLE data_ingestion.earnings_calendar IS 'Upcoming earnings dates and estimates';
COMMENT ON TABLE data_ingestion.esg_scores IS 'ESG (Environmental, Social, Governance) scores and ratings';

COMMENT ON COLUMN data_ingestion.company_info.additional_data IS 'JSONB storage for remaining 150+ info fields from Yahoo API';
COMMENT ON COLUMN data_ingestion.financial_statements.data IS 'Full statement data with 39-68 line items depending on statement type';
```

### Usage Examples

#### Load Market Data Only

```python
from src.services.yahoo.loader import YahooDataLoader

loader = YahooDataLoader(batch_size=100)

# Load OHLCV data
await loader.load_market_data(
    symbol="AAPL",
    start_date=date(2023, 1, 1),
    end_date=date(2024, 1, 1),
    interval="1d"  # '1m', '5m', '1h', '1d', '1wk', '1mo'
)
```

#### Load Company Fundamentals

```python
# Load company profile
await loader.load_company_info(symbol="AAPL")

# Load key statistics
await loader.load_key_statistics(symbol="AAPL")

# Load key statistics with specific date
await loader.load_key_statistics(symbol="AAPL", stats_date=date(2024, 1, 15))

# Load financial statements
await loader.load_financials(
    symbol="AAPL",
    statement_type="income",  # 'income', 'balance_sheet', 'cash_flow'
    period_type="quarterly"   # 'annual', 'quarterly'
)
```

#### Load Corporate Actions

```python
# Load dividends
count = await loader.load_dividends(
    symbol="AAPL",
    start_date=date(2023, 1, 1),
    end_date=date(2024, 1, 1)
)
print(f"Loaded {count} dividends")

# Load stock splits
count = await loader.load_splits(
    symbol="AAPL",
    start_date=date(2020, 1, 1),
    end_date=date(2024, 1, 1)
)
print(f"Loaded {count} stock splits")

# Load analyst recommendations
count = await loader.load_analyst_recommendations(symbol="AAPL")
print(f"Loaded {count} analyst recommendation records")

# Load ESG scores
success = await loader.load_esg_scores(symbol="AAPL")
if success:
    print("ESG scores loaded successfully")
else:
    print("No ESG scores available")
```

#### Load Everything

```python
# Load all available data
await loader.load_all_data(
    symbol="AAPL",
    start_date=date(2023, 1, 1),
    end_date=date(2024, 1, 1),
    include_fundamentals=True,
    include_dividends=True,
    include_splits=True,
    include_analyst_recommendations=True,
    include_esg_scores=True
)
```

### CLI Script

```bash
# Load market data only (default)
python scripts/load_yahoo_data.py --symbol AAPL --days 30

# Load company info only (no market data)
python scripts/load_yahoo_data.py --symbol AAPL --company-info

# Load key statistics only
python scripts/load_yahoo_data.py --symbol AAPL --key-statistics

# Load market data + company info + key statistics
python scripts/load_yahoo_data.py --symbol AAPL --days 30 --market-data --company-info --key-statistics

# Load for all active symbols (market data only)
python scripts/load_yahoo_data.py --all-symbols --days 30

# Load key statistics for all symbols
python scripts/load_yahoo_data.py --all-symbols --key-statistics --max-symbols 10

# Load company info for all symbols
python scripts/load_yahoo_data.py --all-symbols --company-info

# Load multiple data types
python scripts/load_yahoo_data.py --symbol AAPL --days 30 \
    --market-data \
    --company-info \
    --key-statistics \
    --institutional-holders

# Load analyst recommendations only
python scripts/load_yahoo_data.py --symbol AAPL --analyst-recommendations

# Load analyst recommendations for all symbols
python scripts/load_yahoo_data.py --all-symbols --analyst-recommendations

# Load ESG scores only
python scripts/load_yahoo_data.py --symbol AAPL --esg-scores

# Load ESG scores for all symbols
python scripts/load_yahoo_data.py --all-symbols --esg-scores
```

### Rate Limits & Best Practices

**Rate Limits:**
- No official rate limit
- Recommended: 2000 requests/hour (safe limit)
- Implement polite delays (0.5-1 second between requests)
- Use batch processing for multiple symbols

**Best Practices:**
1. **Caching**: Yahoo data changes less frequently than Polygon
2. **Update Frequency**:
   - Market data: Daily (EOD)
   - Fundamentals: Weekly or after earnings
   - Dividends/Splits: Monthly check
3. **Error Handling**: Yahoo API can be flaky, implement retries
4. **Data Validation**: Cross-check with Polygon when available

### Limitations

- ❌ No tick-level data
- ❌ 15-minute delayed real-time data
- ❌ Intraday history limited to 60 days
- ❌ API can be unreliable (no SLA)
- ❌ Data quality varies by symbol
- ⚠️ Unofficial API (could change)

### Best Use Cases

- ✅ Backtesting and research
- ✅ Fundamental analysis
- ✅ Development and testing
- ✅ Long-term historical data (decades)
- ✅ Dividend/split data validation
- ✅ Company research and screening
- ❌ Production real-time trading
- ❌ High-frequency strategies

---

## Data Source Comparison

### Feature Matrix

| Feature | Polygon.io | Yahoo Finance | Alpaca |
|---------|-----------|---------------|---------|
| **OHLCV Data** | ✅ Excellent | ✅ Good | ✅ Good |
| **Real-time** | ✅ Yes | ⚠️ 15-min delay | ✅ Yes |
| **Historical Depth** | 10+ years | 50+ years | 5+ years |
| **Intraday Data** | ✅ All history | ⚠️ 60 days | ✅ All history |
| **Fundamentals** | ❌ No | ✅ Comprehensive | ❌ No |
| **Dividends** | ✅ Yes | ✅ Yes | ❌ No |
| **Splits** | ✅ Yes | ✅ Yes | ❌ No |
| **Options** | ✅ Yes | ✅ Yes | ❌ No |
| **News** | ✅ Yes | ✅ Yes | ✅ Yes |
| **API Stability** | ✅ Excellent | ⚠️ Good | ✅ Excellent |
| **Rate Limits** | 5/min (free) | None (soft) | ✅ Generous |
| **Cost** | $$ Paid | Free | Free |
| **Best For** | Production | Research | Paper Trading |

### When to Use Each Source

**Use Polygon.io for:**
- Production trading systems
- Real-time data needs
- High-frequency strategies
- Accurate corporate actions
- Professional-grade data quality

**Use Yahoo Finance for:**
- Backtesting and research
- Fundamental analysis
- Cost-conscious development
- Long historical data
- Company screening and research

**Use Alpaca for:**
- Paper trading
- Order execution
- Real-time trading (with account)
- Integrated trading and data

### Data Validation Strategy

```python
# Validate by comparing sources
async def validate_market_data(symbol: str, date: date):
    """Compare data from Polygon and Yahoo"""
    
    # Get data from both sources
    polygon_data = await get_market_data(symbol, date, source="polygon")
    yahoo_data = await get_market_data(symbol, date, source="yahoo")
    
    # Compare close prices (should be within 0.5%)
    price_diff = abs(polygon_data.close - yahoo_data.close) / polygon_data.close
    
    if price_diff > 0.005:  # 0.5% threshold
        logger.warning(f"Price discrepancy for {symbol}: {price_diff:.2%}")
        return False
    
    return True
```

---

## Implementation Plan

### Phase 1: Database Setup ✅ COMPLETED
- [x] Add `data_source` column to `market_data` table
- [x] Update unique constraint to `(symbol, timestamp, data_source)`
- [x] Update Python models and loaders
- [x] Update tests

### Phase 2: Yahoo Client & Models
**Files to Create:**
1. `src/services/yahoo/__init__.py`
2. `src/services/yahoo/client.py` (~300 lines)
3. `src/services/yahoo/exceptions.py` (~50 lines)
4. `src/services/yahoo/models.py` (~200 lines)

**Key Classes:**
- `YahooClient`: API wrapper using `yfinance`
- Exception classes: `YahooAPIError`, `YahooDataError`, etc.
- Pydantic models for all data types

**Estimated Effort:** 4-6 hours

### Phase 3: Database Schema
**Files to Create:**
1. `scripts/08_create_yahoo_tables.sql` (~150 lines)
2. `scripts/08_rollback_yahoo_tables.sql` (~50 lines)
3. `src/shared/database/models/company_info.py`
4. `src/shared/database/models/fundamentals.py`
5. `src/shared/database/models/corporate_actions.py`

**Tables:**
- `company_info`
- `key_statistics`
- `dividends`
- `stock_splits`
- `financial_statements`

**Estimated Effort:** 3-4 hours

### Phase 4: Yahoo Loader
**Files to Create:**
1. `src/services/yahoo/loader.py` (~500 lines)

**Key Methods:**
- `load_market_data()`: OHLCV data
- `load_company_info()`: Company profile
- `load_key_statistics()`: Financial metrics
- `load_financials()`: Financial statements
- `load_dividends()`: Dividend history (with date range support)
- `load_splits()`: Stock split history (with date range support)
- `load_analyst_recommendations()`: Analyst recommendation counts over time
- `load_esg_scores()`: ESG (Environmental, Social, Governance) scores
- `load_all_data()`: Comprehensive load
- `load_all_symbols_data()`: Batch processing

**Estimated Effort:** 6-8 hours

### Phase 5: CLI Script
**Files to Create:**
1. `scripts/load_yahoo_data.py` (~400 lines)

**Features:**
- Single symbol or all symbols
- Select data types to load
- Date range specification
- Progress tracking
- Error handling and logging

**Estimated Effort:** 2-3 hours

### Phase 6: Testing
**Files to Create:**
1. `tests/unit/test_yahoo_client.py` (~300 lines)
2. `tests/unit/test_yahoo_loader.py` (~400 lines)
3. `tests/integration/test_yahoo_integration.py` (~200 lines)

**Test Coverage:**
- Client methods (mocked API calls)
- Loader methods (database integration)
- Error handling
- Data validation
- Edge cases

**Estimated Effort:** 4-5 hours

### Phase 7: Documentation
**Files to Update:**
1. This file (already done!)
2. `docs/api/data-ingestion.md`
3. `README.md`
4. Add usage examples

**Estimated Effort:** 1-2 hours

### Total Estimated Effort
**25-35 hours** (~1 week of focused development)

---

## Best Practices

### Data Freshness

```python
# Recommended update schedules

# Market Data
Polygon: Intraday (real-time)
Yahoo:   Daily EOD
Alpaca:  Intraday (real-time)

# Fundamentals (Yahoo only)
Company Info:      Weekly or on-demand
Key Statistics:    Daily EOD
Financial Statements: Quarterly + after earnings
Dividends:         Monthly check
Splits:           Monthly check
```

### Error Handling

```python
from src.services.yahoo.exceptions import YahooAPIError, YahooDataError

try:
    data = await yahoo_client.get_historical_data("AAPL", start, end)
except YahooAPIError as e:
    # API connection issues, rate limits
    logger.error(f"Yahoo API error: {e}")
    # Fall back to Polygon if available
    data = await polygon_client.get_aggregates("AAPL", start, end)
except YahooDataError as e:
    # Data quality issues
    logger.warning(f"Yahoo data quality issue: {e}")
    # Skip this symbol or mark for manual review
```

### Data Quality Checks

```python
async def validate_data_quality(symbol: str, bars: List[YahooBar]):
    """Validate Yahoo data quality"""
    
    checks = []
    
    # Check for gaps
    has_gaps = check_for_date_gaps(bars)
    checks.append(("no_gaps", not has_gaps))
    
    # Check for zero/negative prices
    has_bad_prices = any(b.close <= 0 for b in bars)
    checks.append(("valid_prices", not has_bad_prices))
    
    # Check for zero volume
    has_zero_volume = any(b.volume == 0 for b in bars)
    checks.append(("valid_volume", not has_zero_volume))
    
    # Check OHLC logic
    has_valid_ohlc = all(
        b.high >= max(b.open, b.close) and 
        b.low <= min(b.open, b.close)
        for b in bars
    )
    checks.append(("valid_ohlc", has_valid_ohlc))
    
    # Log results
    failed = [name for name, passed in checks if not passed]
    if failed:
        logger.warning(f"{symbol}: Failed quality checks: {failed}")
    
    return len(failed) == 0
```

### Caching Strategy

```python
# Cache company info (changes rarely)
from functools import lru_cache

@lru_cache(maxsize=1000)
async def get_company_info_cached(symbol: str):
    """Cache company info for 24 hours"""
    return await yahoo_client.get_company_info(symbol)

# Cache fundamentals (changes daily)
# Use Redis for distributed caching
await redis_client.setex(
    f"fundamentals:{symbol}",
    86400,  # 24 hours
    json.dumps(fundamentals.dict())
)
```

### Query Patterns

```sql
-- Get latest data from preferred source with fallback
SELECT 
    symbol,
    timestamp,
    close,
    volume,
    data_source
FROM data_ingestion.market_data
WHERE symbol = 'AAPL'
AND timestamp >= '2024-01-01'
AND data_source = COALESCE(
    (SELECT 'polygon' WHERE EXISTS (
        SELECT 1 FROM data_ingestion.market_data 
        WHERE symbol = 'AAPL' AND data_source = 'polygon'
    )),
    'yahoo'
)
ORDER BY timestamp DESC;

-- Compare prices across sources
SELECT 
    m1.symbol,
    m1.timestamp,
    m1.close as polygon_close,
    m2.close as yahoo_close,
    ABS(m1.close - m2.close) / m1.close * 100 as diff_pct
FROM data_ingestion.market_data m1
JOIN data_ingestion.market_data m2 
    ON m1.symbol = m2.symbol 
    AND m1.timestamp = m2.timestamp
WHERE m1.data_source = 'polygon'
AND m2.data_source = 'yahoo'
AND m1.symbol = 'AAPL'
AND ABS(m1.close - m2.close) / m1.close > 0.01  -- More than 1% difference
ORDER BY m1.timestamp DESC;

-- Get comprehensive company data
SELECT 
    c.symbol,
    c.name,
    c.sector,
    c.industry,
    k.market_cap,
    k.pe_ratio,
    k.earnings_per_share,
    k.dividend_yield
FROM data_ingestion.company_info c
LEFT JOIN data_ingestion.key_statistics k 
    ON c.symbol = k.symbol
WHERE k.date = (
    SELECT MAX(date) FROM data_ingestion.key_statistics
    WHERE symbol = c.symbol
)
AND c.sector = 'Technology'
ORDER BY k.market_cap DESC;
```

### Monitoring & Alerts

```python
# Set up alerts for data quality issues

async def monitor_data_loads():
    """Monitor daily data loads"""
    
    # Check for failed loads
    failed_loads = await get_failed_loads(date.today())
    if len(failed_loads) > 5:
        send_alert(f"Multiple failed loads: {len(failed_loads)}")
    
    # Check for stale data
    stale_symbols = await get_stale_symbols(max_age_days=2)
    if len(stale_symbols) > 10:
        send_alert(f"Stale data for {len(stale_symbols)} symbols")
    
    # Check for price discrepancies
    discrepancies = await compare_sources_today()
    if len(discrepancies) > 5:
        send_alert(f"Price discrepancies: {len(discrepancies)}")
```

---

## Next Steps

1. ✅ Review this documentation
2. ⏳ Run Phase 1 migration (add `data_source` column)
3. ⏳ Implement Phase 2 (Yahoo Client)
4. ⏳ Implement Phase 3 (Database Schema)
5. ⏳ Implement Phase 4 (Yahoo Loader)
6. ⏳ Implement Phase 5 (CLI Script)
7. ⏳ Implement Phase 6 (Testing)
8. ⏳ Update remaining documentation

## Questions & Considerations

**Questions to Address:**
1. Should we implement automatic source fallback?
2. Do we need real-time reconciliation between sources?
3. Should fundamentals be loaded on a schedule or on-demand?
4. Do we want to track data quality metrics over time?
5. Should we implement a "preferred source" configuration per symbol?

**Technical Decisions:**
1. Use `yfinance` library (most popular, well-maintained)
2. Store financial statements as JSONB (flexible schema)
3. Separate loader classes (better separation of concerns)
4. UTC timezone for all timestamps (consistency)
5. Batch processing for multiple symbols (efficiency)

---

*Last Updated: December 2025*
*Author: Trading System Team*

