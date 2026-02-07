# Data Sources Overview

> **📋 Implementation Status**: ✅ Core Features Implemented (v1.0.0)

This document provides a high-level overview of the multi-source data integration architecture for the trading system.

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

For detailed integration guides, see:
- [Polygon.io Integration](data-sources-polygon.md)
- [Yahoo Finance Integration](data-sources-yahoo.md)
- [Data Source Comparison](data-sources-comparison.md)

---

## Multi-Source Architecture

### Design Principles

1. **Independent Services**: Each data source has its own service module
2. **Unified Storage**: All market data stored in `data_ingestion.market_data` with `data_source` field (e.g. `yahoo`, `yahoo_adjusted`, `polygon`, `alpaca`)
3. **Source Tracking**: Track which provider supplied each data point; Yahoo stores both unadjusted (`yahoo`) and adjusted (`yahoo_adjusted`) OHLCV
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

## Related Documentation

- [Polygon.io Integration](data-sources-polygon.md): Detailed Polygon.io integration guide
- [Yahoo Finance Integration](data-sources-yahoo.md): Comprehensive Yahoo Finance integration guide
- [Data Source Comparison](data-sources-comparison.md): Feature comparison and best practices
- [Implementation Plan](data-sources-implementation.md): Yahoo Finance implementation phases

---

**Last Updated**: December 2025  
**Status**: ✅ Core Features Implemented (v1.0.0)

