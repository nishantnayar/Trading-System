# Stock Screener with AI Analysis

The Stock Screener is an AI-powered tool that helps you find stocks matching specific criteria using natural language queries or traditional filters. It integrates with local LLM (Ollama) to provide intelligent query interpretation and analysis.

## Overview

The Stock Screener allows you to:
- **Search with Natural Language**: Ask questions like "Find tech stocks with RSI below 30"
- **Use Traditional Filters**: Apply precise filters for sector, price, volume, RSI, etc.
- **Get AI Analysis**: Receive intelligent insights about your screening results
- **Export Results**: Download filtered stocks as CSV for further analysis

## Features

### 🤖 Natural Language Queries
Ask questions in plain English and let the AI interpret your requirements:
- "Find undervalued tech stocks with high volume"
- "Show me healthcare stocks with RSI between 30 and 70"
- "Find stocks with price between $50 and $200 in the finance sector"

### ⚙️ Traditional Filters
Use precise controls for exact filtering:
- **Sector & Industry**: Filter by business sector and industry
- **Price Range**: Set minimum and maximum price filters
- **Volume**: Filter by average trading volume
- **Market Cap**: Set minimum market capitalization
- **Technical Indicators**: Filter by RSI, price changes, volatility
- **Time-based Filters**: Filter by price changes over different periods

### 📊 Technical Indicators
The screener calculates and displays:
- **RSI (Relative Strength Index)**: Momentum indicator (0-100)
- **MACD**: Moving Average Convergence Divergence
- **Moving Averages**: SMA 20, SMA 50
- **Price Changes**: 1-day, 5-day, 30-day percentage changes
- **Volatility**: Annualized volatility percentage
- **Bollinger Bands Position**: Price position relative to bands

### 🧠 AI-Powered Analysis
Get intelligent insights about your screening results:
- Pattern recognition in results
- Notable opportunities or risks
- Sector distribution analysis
- Key observations and recommendations

## How to Use

### Accessing the Screener

1. Start your Streamlit application:
   ```bash
   streamlit run streamlit_ui/streamlit_app.py
   ```

2. Navigate to the **Screener** page from the sidebar menu

### Using Natural Language Queries

1. Click on the **"🤖 Natural Language Query"** tab
2. Enter your query in the text box:
   ```
   Find tech stocks with RSI below 30 and volume above 1 million
   ```
3. Click **"🔍 Search"**
4. The AI will interpret your query and show the parsed criteria
5. Review the matching stocks in the results table
6. Expand **"🤖 AI Analysis"** to see intelligent insights

**Example Queries:**
- `Find tech stocks with RSI < 30`
- `Show me high volume stocks in healthcare sector`
- `Find stocks with price between $50 and $200`
- `Show undervalued stocks with low volatility`

### Using Traditional Filters

1. Click on the **"⚙️ Traditional Filters"** tab
2. Set your filter criteria:
   - **Sector & Industry**: Select from dropdowns
   - **Price & Volume**: Enter numeric ranges
   - **Technical Indicators**: Use sliders and inputs
3. Click **"🔍 Apply Filters"**
4. Review results in the table below

**Filter Options:**

| Filter | Description | Example |
|--------|-------------|---------|
| Sector | Business sector | Technology, Healthcare, Finance |
| Industry | Specific industry | Software, Biotechnology, Banking |
| Min Price | Minimum stock price | $10.00 |
| Max Price | Maximum stock price | $500.00 |
| Min Volume | Minimum average volume | 1,000,000 |
| Min Market Cap | Minimum market cap (billions) | $1.0B |
| RSI Range | RSI value range | 30-70 |
| Price Change | 30-day price change % | -10% to +20% |

### Understanding Results

The results table displays:

| Column | Description |
|--------|-------------|
| Symbol | Stock ticker symbol |
| Name | Company name |
| Sector | Business sector |
| Industry | Industry classification |
| Price | Current stock price |
| RSI | Relative Strength Index (0-100) |
| Price Chg (30d) | 30-day price change percentage |
| Volatility | Annualized volatility % |
| Avg Volume | Average trading volume |
| Market Cap | Market capitalization |

### Exporting Results

1. After screening, scroll to the bottom of the results
2. Click **"📥 Download Results as CSV"**
3. The file will be named: `stock_screener_results_YYYYMMDD_HHMMSS.csv`

## Technical Details

### Screening Process

1. **Symbol Loading**: Fetches available symbols from the database
2. **Data Retrieval**: Gets market data and company info for each symbol
3. **Indicator Calculation**: 
   - **Database-First**: Attempts to load pre-calculated indicators from database (fast)
   - **Fallback Calculation**: Calculates indicators on-the-fly if not in database
4. **Filtering**: Applies your criteria to filter stocks
5. **Results Display**: Shows matching stocks in an interactive table
6. **AI Analysis**: Generates insights using local LLM (if available)

### Technical Indicators Storage Strategy

The screener uses a **hybrid approach** for technical indicators:

#### Database-Backed Indicators (Recommended)

**Benefits:**
- ⚡ **10-100x Faster**: Pre-calculated indicators eliminate per-symbol calculations
- 📊 **Historical Tracking**: Store indicator values over time for analysis
- 🔍 **Direct SQL Filtering**: Filter by RSI, MACD directly in database queries
- 📈 **Scalability**: Handle thousands of symbols efficiently
- ✅ **Consistency**: Same calculation method for all queries

**Storage Approach:**
- **Latest Values Table**: Fast access to current indicator values for screening
- **Time-Series Table**: Historical indicator values for backtesting and analysis
- **Daily Calculation Jobs**: Automated calculation and storage of indicators

**Indicators Stored:**
- Moving Averages (SMA 20, 50, 200; EMA 12, 26)
- Momentum Indicators (RSI, RSI-14)
- MACD (Line, Signal, Histogram)
- Bollinger Bands (Upper, Middle, Lower, Position)
- Volatility (20-day annualized, ATR-14)
- Price Changes (1d, 5d, 30d, 90d)
- Volume Metrics (SMA-20, Volume Ratio)

**Calculation Service:**
- Batch processes indicators from market data
- Handles missing data gracefully
- Updates both latest and historical tables
- Can run as scheduled daily job or on-demand

#### Fallback Calculation

If indicators are not available in the database:
- Calculates indicators on-the-fly using Python functions
- Uses same calculation logic for consistency
- Results are not stored (for performance, use database approach)

### Performance Considerations

**Current Implementation:**
- **Symbol Limit**: Screens up to 50 symbols at a time (for demo purposes)
- **Processing Time**: 
  - With database: ~0.1-0.5 seconds per symbol (10-50x faster)
  - Without database: ~1-2 seconds per symbol (calculation overhead)
- **Caching**: Company info and sectors are cached for faster loading
- **LLM Processing**: AI analysis adds ~2-5 seconds depending on model

**With Database Storage:**
- **Screening Speed**: Can screen 1000+ symbols in seconds
- **Query Performance**: Direct SQL filtering on RSI, MACD, etc.
- **Storage Overhead**: ~50-100 bytes per symbol per day (~18-36 MB/year for 1000 symbols)

**Migration Path:**
1. Database tables created (no breaking changes)
2. Calculation service populates indicators
3. Screener automatically uses database when available
4. Falls back to calculation if database values missing

### Requirements

- **Ollama**: Must be installed and running for natural language queries
- **Model**: Requires at least one model (recommended: `phi3`)
- **API Connection**: Trading System API must be running
- **Market Data**: Requires market data in the database

## Troubleshooting

### No Results Found

**Possible Causes:**
- Criteria too restrictive
- No symbols match all filters
- Market data not available for symbols

**Solutions:**
- Relax filter criteria
- Try broader sector/industry selections
- Check if market data is loaded in database

### LLM Not Working

**Symptoms:**
- Warning message: "LLM service not available"
- Natural language queries don't work

**Solutions:**
1. Verify Ollama is running:
   ```bash
   ollama list
   ```
2. Check if a model is installed:
   ```bash
   ollama pull phi3
   ```
3. Test Ollama connection:
   ```bash
   python scripts/test_ollama.py
   ```

### Slow Performance

**Causes:**
- Large number of symbols to screen
- Network latency to API
- LLM processing time

**Solutions:**
- Reduce number of symbols (currently limited to 50)
- Use traditional filters instead of natural language (faster)
- Ensure API is running locally for faster response

### Missing Technical Indicators

**Causes:**
- Insufficient historical data
- Symbol has limited trading history
- Data quality issues

**Solutions:**
- Ensure sufficient historical data is loaded
- Check data quality in database
- Some indicators require minimum data points (e.g., RSI needs 15+ days)

## Best Practices

### Query Formulation

**Good Queries ✅**

- "Find tech stocks with RSI below 30"
- "Show me healthcare stocks with high volume"
- "Find stocks with price between $50 and $200"

**Less Effective:**
- ❌ "Good stocks" (too vague)
- ❌ "Find everything" (no criteria)
- ❌ Very complex multi-part queries (may not parse correctly)

### Filter Strategy

1. **Start Broad**: Begin with sector/industry filters
2. **Add Technical**: Apply RSI or price change filters
3. **Refine**: Narrow down with volume or market cap
4. **Review**: Check AI analysis for insights

### Result Analysis

1. **Review AI Insights**: Check the AI analysis section for patterns
2. **Sort Columns**: Use table sorting to find top performers
3. **Export for Analysis**: Download CSV for deeper analysis in Excel/Python
4. **Cross-Reference**: Compare with other analysis tools

## Examples

### Example 1: Finding Oversold Tech Stocks

**Query:**
```
Find technology stocks with RSI below 30 and volume above 500,000
```

**What it does:**
- Filters to Technology sector
- Finds stocks with RSI < 30 (oversold condition)
- Requires minimum volume of 500,000
- Identifies potential buying opportunities

### Example 2: High-Growth Healthcare Stocks

**Traditional Filters:**
- Sector: Healthcare
- Min Price Change (30d): 10%
- Min Market Cap: $1.0B
- RSI: 40-70

**What it finds:**
- Healthcare stocks with strong recent performance
- Established companies (market cap filter)
- Not overbought (RSI < 70)
- Potential momentum plays

### Example 3: Value Stocks

**Query:**
```
Find stocks with price between $20 and $100, low volatility, and positive 30-day change
```

**What it identifies:**
- Stocks in reasonable price range
- Low volatility (less risky)
- Positive momentum (recent gains)
- Potential value opportunities

## Integration with Other Features

### Analysis Page
- Select a symbol from screener results
- Navigate to Analysis page for detailed charts
- View technical indicators and company info

### Portfolio Management
- Use screener to find potential additions
- Export results for portfolio planning
- Cross-reference with existing holdings

## Future Enhancements

Planned improvements:
- **Database-Backed Indicators**: Store pre-calculated indicators for 10-100x faster screening
- **More Symbols**: Increase screening limit (1000+ with database storage)
- **Advanced Filters**: More technical indicators (Stochastic, ADX, etc.)
- **Saved Screens**: Save and reuse filter combinations
- **Alerts**: Set up alerts for matching criteria or indicator crossovers
- **Backtesting**: Test screening strategies historically using stored indicators
- **Custom Indicators**: Add user-defined indicators
- **Real-Time Updates**: Automatic indicator recalculation on new market data
- **Indicator History**: Track indicator changes over time for pattern analysis

## Technical Documentation

For developers and technical details:
- **[Stock Screener Architecture](../development/stock-screener-architecture.md)** - Complete technical documentation, architecture overview, component breakdown, data flow, and implementation details

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review system logs for errors
3. Verify API and Ollama connections
4. Test with `python scripts/test_ollama.py`

---

**Last Updated**: 2025-01-16  
**Version**: 1.0.0

