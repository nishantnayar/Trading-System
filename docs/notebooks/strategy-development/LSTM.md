# LSTM Model for Stock Price Prediction

This notebook trains an LSTM (Long Short-Term Memory) neural network to predict stock prices using historical OHLCV data from the trading system database.

## Objectives

- Load historical market data from PostgreSQL
- Use pre-calculated technical indicators from database
- Create time-aware train/validation/test splits
- Train an LSTM model using PyTorch with optimized hyperparameters
- Predict log returns (stationary target) instead of raw prices
- Use Huber Loss (robust to outliers) instead of MSE
- Monitor directional accuracy (key trading metric) during training
- Evaluate model performance with financial metrics
- Visualize predictions and residuals

---

## Experiment Progress Log

### Phase 1: Setup and Data Loading ✅

#### Step 1.1: Environment Setup

**Status:** ✅ Completed

**Actions Taken:**

- Configured project path and environment variable loading
- Set up random seeds (RANDOM_SEED = 42) for reproducibility across NumPy, PyTorch, and CUDA
- Verified CUDA availability (NVIDIA GeForce RTX 3050 Laptop GPU detected)

**Rationale:**

- Reproducibility is critical for ML experiments - fixed random seeds ensure consistent results across runs
- CUDA enables GPU acceleration for faster LSTM training
- Environment variables loaded from `.env` file for secure database credential management

#### Step 1.2: Data Loading Function

**Status:** ✅ Completed

**Actions Taken:**

- Created `load_market_data_with_indicators()` function that:
  - Loads OHLCV data from `market_data` table
  - Joins with pre-calculated technical indicators from `analytics.technical_indicators` table
  - Filters by symbol, date range, and data source
  - Validates minimum record count (default: 1000 records)
  - Only includes complete OHLCV records (`is_complete = True`)

**Rationale:**

- Pre-calculated technical indicators save computation time and ensure consistency
- Database joins on date ensure proper alignment between market data and indicators
- Minimum record requirement prevents training on insufficient data
- Complete OHLCV records ensure data quality

**Data Loaded:**

- Symbol: MU (Micron Technology)
- Data Source: Yahoo Finance
- Records: 1,731 market data records, 365 technical indicator records
- Date Range: 2024-12-23 to 2025-12-19
- Features: 34 total features including OHLCV, moving averages, RSI, MACD, Bollinger Bands, volatility metrics, and derived ratios

#### Step 1.3: Data Quality Checks

**Status:** ✅ Completed

**Actions Taken:**

- Identified missing values: 1 in `returns`, 1 in `log_returns` (expected from `.pct_change()` and `.shift()` operations)
- Removed rows with null values (1 row removed, final dataset: 1,730 records)
- Verified data types and structure

**Rationale:**

- Missing values in returns are expected (first row has no previous value to calculate return)
- Removing nulls ensures clean dataset for LSTM training
- Data quality validation prevents downstream errors

---

### Phase 2: Target Transformation ✅

#### Step 2.1: Target Variable Creation

**Status:** ✅ Completed

**Actions Taken:**

- Renamed existing `returns` column to `target_pct_return` (percentage returns)
- Renamed existing `log_returns` column to `target_log_return` (log returns)
- Stored original close prices in `close_original` for inverse transformation

**Rationale:**

**Why predict returns instead of prices?**

- Returns are more stationary than prices (prices have trends, returns are mean-reverting)
- Returns are scale-invariant (10% return is meaningful regardless of price level)
- Returns align better with trading decisions (direction and magnitude of change)

**Why log returns over percentage returns?**

- Log returns are symmetric (log(1.1) ≈ -log(0.9))
- Log returns are additive over time (multi-period return = sum of single-period returns)
- Log returns are theoretically preferred in financial modeling
- Both are available for comparison

**Target Variables Created:**

- `target_pct_return`: Percentage return = (P_t - P_{t-1}) / P_{t-1}
- `target_log_return`: Log return = ln(P_t / P_{t-1})

#### Step 2.2: Inverse Transformation Functions

**Status:** ✅ Completed

**Actions Taken:**

- Created `inverse_transform_pct_return()`: Converts percentage return predictions back to prices
- Created `inverse_transform_log_return()`: Converts log return predictions back to prices

**Rationale:**

- Model predicts returns, but we need price predictions for evaluation and trading
- Inverse transformation allows conversion: `predicted_price = base_price * (1 + pct_return)` or `base_price * exp(log_return)`
- Essential for backtesting and real-world deployment

---

### Phase 3: Stationarity Analysis ✅

#### Step 3.1: Augmented Dickey-Fuller (ADF) Test

**Status:** ✅ Completed

**Actions Taken:**

- Performed ADF test on `target_log_return` series
- Test statistic: -14.682042
- p-value: 0.000000 (< 0.05)
- Number of lags: 6 (automatically selected via AIC)
- Observations: 1,723

**Results:**

- ✅ **NULL HYPOTHESIS REJECTED** (p-value < 0.05)
- ✅ **Series is STATIONARY**
- ✅ Test statistic < 1% critical value (-3.434151) → Strong evidence (99% confidence)

**Rationale:**

**Why test for stationarity?**

- LSTMs require stationary data to learn meaningful patterns
- Non-stationary data (with trends/unit roots) can lead to spurious correlations
- Stationary series have constant mean and variance over time

**Why ADF test?**

- Formal statistical test for unit root (non-stationarity)
- Standard test in financial time series analysis
- p-value < 0.05 confirms stationarity (rejects null hypothesis of unit root)

**Decision:** ✅ Proceed with `target_log_return` - confirmed stationary, safe for LSTM training

---

### Phase 4: Volatility Clustering Analysis ✅

#### Step 4.1: Volatility Clustering Detection

**Status:** ✅ Completed

**Actions Taken:**

- Calculated rolling volatility (20-day, 60-day, 120-day windows)
- Visualized:
  - Log returns over time
  - Rolling volatility (20-day window)
  - Squared returns (volatility proxy)
- Performed Ljung-Box test on squared returns (tests for ARCH effects)

**Results:**

**Rolling Volatility Statistics (20-day):**

- Mean: 0.013062
- Std Dev: 0.006256
- Min: 0.003538
- Max: 0.042102
- **Range Ratio: 11.90x** (significant variation!)

**Ljung-Box Test:**

- Test Statistic: 144.2582
- p-value: 0.000000 (< 0.05)
- ✅ **VOLATILITY CLUSTERING DETECTED**
- ✅ **Heteroskedasticity confirmed** (variance NOT constant over time)

**Rationale:**

**What is volatility clustering?**

- Periods of high volatility followed by high volatility
- Periods of low volatility followed by low volatility
- Common in financial markets (e.g., market crashes, calm periods)

**Commentary:**

The detection of **Volatility Clustering** (p-value: 0.000000) is a critical finding. It confirms that your data has "memory" in its variance—periods of high volatility are followed by high volatility, and calm periods follow calm periods.

This is actually **good news** for an LSTM model, as LSTMs are specifically designed to capture these types of long-term dependencies that simpler models (like ARIMA) struggle with.

**Why does it matter?**

- If training set has low volatility but test set has high volatility, model may struggle
- Variance mismatch between train/test can degrade model performance
- LSTMs handle this better than linear models (ARIMA), but scaling is still critical

#### Step 4.2: Scaling Strategy Decision

**Status:** ✅ Decision Made

**Recommendation:** Use RobustScaler for input features (X)

**Rationale:**

Since we have confirmed the variance is not constant (heteroskedasticity), a standard MinMaxScaler might be "crushed" by a few high-volatility days (outliers).

**Why RobustScaler?**

- RobustScaler uses the Median and the Interquartile Range (IQR) instead of the Mean and Standard Deviation
- This prevents a single volatile week from shrinking all your other data into a tiny, unusable range
- More robust to outliers than StandardScaler or MinMaxScaler

**Target (y) Scaling:**

- Keep `target_log_return` unscaled or use very light scaling that preserves the 0-center
- Returns are already normalized and centered around zero
- Additional scaling may not be necessary and could distort the signal

**Decision:** ⚠️ **Use RobustScaler for features (X), keep target (y) unscaled**

---

## Key Findings So Far

### ✅ Confirmed Stationary Target

- `target_log_return` passes ADF test (p-value < 0.05)
- Safe for LSTM training without differencing

### ⚠️ Volatility Clustering Detected

- Significant volatility variation (11.9x range ratio)
- Ljung-Box test confirms ARCH effects (p-value < 0.05)
- **Action Required:** Implement RobustScaler for input features before model training

### 📊 Dataset Characteristics

- **Symbol:** MU (Micron Technology)
- **Records:** 1,730 (after null removal)
- **Features:** 34 total (OHLCV + 29 technical indicators)
- **Date Range:** ~1 year of hourly data
- **Target:** Log returns (stationary, confirmed)

---

## Technical Decisions Summary

| Decision | Rationale | Status |
|----------|-----------|--------|
| Predict returns, not prices | Returns are stationary; prices have trends | ✅ Implemented |
| Use log returns | Symmetric, additive, theoretically preferred | ✅ Implemented |
| Remove null rows | Clean data required for LSTM | ✅ Implemented |
| ADF test for stationarity | Formal validation before training | ✅ Passed |
| Check volatility clustering | Identifies need for scaling | ✅ Detected |
| Use RobustScaler for features | Required due to volatility clustering and outliers | ⚠️ To be implemented |
| Keep target unscaled | Returns already normalized, preserve 0-center | ⚠️ To be implemented |
| Store original prices | Needed for inverse transformation | ✅ Implemented |

---

## Notes

- All timestamps stored in UTC (database requirement)
- Data displayed in Central Timezone for user convenience
- Random seed set to 42 for reproducibility
- CUDA available for GPU acceleration
