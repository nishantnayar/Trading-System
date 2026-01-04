# Alpaca Integration

## Overview

Alpaca Markets provides real-time trading data and account information for live trading operations. The integration supports account management, position tracking, order execution, and trade monitoring.

**Status**: ✅ Implemented (v1.0.0)  
**Data Type**: Real-time account data, positions, orders, trades  
**Use Case**: Live trading operations, position management, order execution

## Existing Implementation

- **Client**: Located in `src/services/alpaca/client.py`
- **Rate Limiting**: 200 calls/minute
- **Data Types**: Account, positions, orders, trades
- **Integration**: Already integrated with trading system

## Capabilities

### Account Data
- Account balance and equity
- Buying power and cash
- Account status and trading permissions
- Portfolio value and performance

### Position Management
- Current positions with quantities
- Average entry prices
- Unrealized P&L
- Market values

### Order Management
- Order placement (market, limit, stop)
- Order status tracking
- Order history
- Execution monitoring

### Trade Data
- Trade execution details
- Fill prices and quantities
- Commission tracking
- Settlement information

## Integration Details

### Client Implementation

The Alpaca client is located in `src/services/alpaca/client.py` and provides:
- Account information retrieval
- Position management
- Order placement and tracking
- Trade execution monitoring

### Prefect Flows

Alpaca data ingestion uses the following Prefect flows:

1. **Account Monitoring Flow**: Monitors account status and positions
2. **Order Monitoring Flow**: Tracks active orders and executions

See [Data Ingestion Overview](data-ingestion-overview.md#prefect-flows) for flow implementation details.

### Data Storage

- **PostgreSQL**: Account data, positions, orders, and trades stored in respective tables
- **Redis**: Real-time account and position data cached
- **Data Source Tag**: All Alpaca data tagged appropriately

## Configuration

### Environment Variables

```bash
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading
# ALPACA_BASE_URL=https://api.alpaca.markets  # Live trading
ALPACA_UPDATE_INTERVAL=60  # 1 minute (real-time)
```

### Settings

```python
class AlpacaSettings(BaseSettings):
    alpaca_api_key: str = Field(default="", alias="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", alias="ALPACA_SECRET_KEY")
    alpaca_base_url: str = Field(default="https://paper-api.alpaca.markets", alias="ALPACA_BASE_URL")
    alpaca_update_interval: int = Field(default=60, alias="ALPACA_UPDATE_INTERVAL")
```

## Usage Examples

### Account Monitoring

```python
from prefect import flow
from src.services.alpaca.client import AlpacaClient

@flow(name="alpaca_account_monitoring")
async def monitor_account():
    client = AlpacaClient()
    
    # Get account information
    account = await client.get_account()
    
    # Get current positions
    positions = await client.get_positions()
    
    # Update cache
    await update_account_cache(account, positions)
```

### Order Monitoring

```python
@flow(name="alpaca_order_monitoring")
async def monitor_orders():
    client = AlpacaClient()
    
    # Get active orders
    active_orders = await client.get_orders(status="open")
    
    # Get filled orders
    filled_orders = await client.get_orders(status="filled")
    
    # Process order updates
    for order in filled_orders:
        await process_order_execution(order)
```

## Enhancement Plan

### Planned Improvements

- **Standardize Data Models**: Align Alpaca data models with other providers
- **Data Quality Monitoring**: Add data quality checks for Alpaca data
- **Caching Layer**: Implement Redis caching for frequently accessed data
- **Error Recovery**: Add robust error recovery mechanisms
- **WebSocket Support**: Real-time streaming for orders and positions (future)

## Best Practices

1. **Rate Limiting**: Respect 200 calls/minute limit
2. **Error Handling**: Implement retry logic for transient errors
3. **Data Validation**: Validate all data before storage
4. **Real-Time Updates**: Use appropriate update intervals for real-time data
5. **Paper Trading**: Test with paper trading before live trading

## Integration with Trading System

Alpaca integration is used for:
- Real-time account monitoring
- Position tracking and management
- Order execution and monitoring
- Trade reconciliation

The Alpaca client integrates with:
- Execution Service: Order placement and tracking
- Analytics Service: Position and performance tracking
- Risk Management: Position limits and exposure monitoring

## Limitations

- **API Rate Limits**: 200 calls/minute may be limiting for high-frequency operations
- **Paper Trading**: Paper trading environment may have different behavior than live
- **Data Latency**: Network latency affects real-time data freshness

## Future Enhancements

- WebSocket streaming for real-time updates
- Advanced order types (bracket orders, OCO orders)
- Portfolio analytics integration
- Multi-account support

---

**See Also**:
- [Data Ingestion Overview](data-ingestion-overview.md) - Overall architecture and common patterns
- [Polygon.io Integration](data-ingestion-polygon.md) - Historical data integration
- [Yahoo Finance Integration](data-ingestion-yahoo.md) - Fundamental data integration

