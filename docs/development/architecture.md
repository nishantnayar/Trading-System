# Trading System Architecture

> **Status**: ✅ Core Features Implemented (v1.0.0) | 🚧 Enhanced Features In Progress (v1.1.0)

## Overview

This is the main architecture documentation index for the Trading System. The architecture documentation has been split into focused documents for better maintainability and navigation.

## Architecture Documents

### Core Architecture

- **[Architecture Overview](architecture-overview.md)** - System overview, requirements, technology stack, communication patterns, security, monitoring, development workflow, configuration, performance, and future enhancements

- **[Services Architecture](architecture-services.md)** - Detailed breakdown of all six microservices (Data Ingestion, Strategy Engine, Execution, Risk Management, Analytics, Notification)

- **[Database Architecture](architecture-database.md)** - Database connectivity strategy, schema design, and concurrent access patterns

- **[UI Architecture](architecture-ui.md)** - Frontend design, Streamlit components, and backend API architecture

### Specialized Architecture

- **[Prefect Architecture](architecture-prefect.md)** - Prefect 3.4.14 orchestration strategy, service-specific flows, deployment configuration, and implementation plan

- **[Deployment Architecture](architecture-deployment.md)** - Local deployment strategy, service deployment, startup scripts, health monitoring, and production considerations

- **[Timezone Architecture](architecture-timezone.md)** - Comprehensive timezone handling strategy for UTC storage, EST trading operations, and CST user interface

## Quick Navigation

| Document | Focus Area | Lines |
|----------|------------|-------|
| [Overview](architecture-overview.md) | System overview, tech stack, communication | ~200 |
| [Services](architecture-services.md) | Microservices breakdown | ~150 |
| [Database](architecture-database.md) | Database design and connectivity | ~250 |
| [UI](architecture-ui.md) | Frontend and API architecture | ~120 |
| [Prefect](architecture-prefect.md) | Workflow orchestration | ~1,250 |
| [Deployment](architecture-deployment.md) | Deployment strategy | ~380 |
| [Timezone](architecture-timezone.md) | Timezone handling | ~460 |

## Architecture Summary

The Trading System is a production-grade algorithmic trading system designed for local deployment, focusing on equities trading through Alpaca with paper trading capabilities. The system uses:

- **Microservices Architecture**: Six core services orchestrated by Prefect
- **Technology Stack**: Python 3.11+, PostgreSQL, Redis, Prefect, Streamlit, FastAPI
- **Data Sources**: Polygon.io, Yahoo Finance, Alpaca API
- **Deployment**: Local machine (Windows 10) with all services running on a single machine
- **Orchestration**: Prefect 3.4.14 for workflow management
- **Frontend**: Streamlit multipage interface with Plotly visualizations

## Status by Component

| Component | Status | Version |
|-----------|--------|---------|
| **Data Ingestion** | ✅ Implemented | v1.0.0 |
| **Execution** | ✅ Implemented | v1.0.0 |
| **Analytics** | ✅ Implemented | v1.0.0 |
| **UI** | ✅ Implemented | v1.0.0 |
| **Strategy Engine** | 🚧 Planned | v1.1.0 |
| **Risk Management** | 🚧 Planned | v1.1.0 |
| **Notification** | 🚧 Planned | v1.1.0 |
| **Prefect Integration** | ✅ Phase 1 Complete | v1.0.0 |

## Related Documentation

- [Database Architecture Detailed Review](database.md) - Comprehensive database documentation
- [Logging Architecture](logging.md) - Logging strategy and implementation
- [Stock Screener Architecture](stock-screener-architecture.md) - Stock screener implementation
- [Prefect Deployment Guide](prefect-deployment-guide.md) - Detailed Prefect deployment instructions
- [Prefect Deployment Plan](prefect-deployment-plan.md) - Prefect implementation roadmap

---

**Last Updated**: December 2025  
**Author**: Nishant Nayar  
**Repository**: https://github.com/nishantnayar/trading-system
