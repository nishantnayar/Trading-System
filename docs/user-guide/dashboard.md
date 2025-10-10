# Dashboard Overview

This guide covers the main dashboard interface and the reusable card components used throughout the application.

## Features

- **Real-time Portfolio Monitoring**: Live account balance, positions, and P&L tracking
- **Market Data Analytics**: Interactive charts and market data visualization with Plotly
- **Strategy Management**: Configure and monitor trading strategies
- **Performance Metrics**: Comprehensive performance tracking and analytics
- **Order Management**: View and manage open orders and trade history
- **System Health**: Monitor service status and system performance
- **Reusable Card Components**: Consistent styling and user experience

## Dashboard Pages

### 1. Main Dashboard (`/dashboard`)
The primary dashboard provides an overview of your trading system:
- **Portfolio Summary**: Account balance, buying power, and portfolio value
- **Position Overview**: Current holdings with unrealized P&L
- **Order Status**: Open orders and recent trade history
- **Market Status**: Real-time market clock and trading hours
- **System Health**: Service status indicators

### 2. Trading Interface (`/trading`)
Interactive trading interface for order management:
- **Account Information**: Detailed account status and buying power
- **Position Management**: View and close positions
- **Order Placement**: Place new market and limit orders
- **Order History**: Track order status and execution

### 3. Market Analysis (`/analysis`)
Professional multi-pane trading charts with advanced technical analysis:
- **Professional Charts**: Lightweight Charts library for high-performance visualization
- **Multi-Pane Layout**: 
  - Price Chart with candlesticks and moving averages (SMA 20/50)
  - Volume chart with color-coded bars
  - MACD indicator (12, 26, 9) with histogram
  - RSI indicator (14) with overbought/oversold levels
- **Interactive Features**:
  - Synchronized crosshairs across all charts
  - Zoom and pan functionality
  - Theme toggle (Light/Dark mode)
  - Timeframe selection (1W, 1M, 3M, 6M, 1Y)
- **Market Statistics**: Live data cards showing total symbols, records, and last update
- **Real-time Data**: Live price information bar with symbol, price, change, volume, high/low

### 4. Strategy Management (`/strategies`)
Strategy configuration and monitoring:
- **Strategy Overview**: Active and available strategies
- **Performance Tracking**: Strategy-specific performance metrics
- **Configuration**: Strategy parameters and settings
- **Backtesting Results**: Historical strategy performance

### 5. User Profile (`/profile`)
System information and user preferences:
- **System Information**: Version, configuration, and status
- **API Configuration**: Alpaca API settings and connectivity
- **Preferences**: User interface and notification settings

## Reusable Card Components

This section covers the reusable card components located in `src/web/templates/components/` for consistent styling across the application.

### Available Components

#### 1. Card Macro (`card_macro.html`)

Provides Jinja2 macros for different types of cards:

##### `stat_card` - For displaying metrics with values
```jinja2
{% from 'components/card_macro.html' import stat_card %}

{{ stat_card(
    icon='fas fa-wallet',
    title='Total Portfolio Value',
    value='$0.00',
    description='Loading...',
    color='blue',
    value_id='portfolio-value',
    description_id='portfolio-change-text'
) }}
```

##### `feature_card` - For displaying features without values
```jinja2
{% from 'components/card_macro.html' import feature_card %}

{{ feature_card(
    icon='fas fa-database',
    title='Data Ingestion',
    description='Real-time market data processing and storage',
    color='green'
) }}
```

##### `info_card` - For displaying information without icons
```jinja2
{% from 'components/card_macro.html' import info_card %}

{{ info_card(
    title='System Status',
    content='All systems operational',
    color='green'
) }}
```

##### `large_stat_card` - For prominent metrics
```jinja2
{% from 'components/card_macro.html' import large_stat_card %}

{{ large_stat_card(
    icon='fas fa-chart-line',
    title='Total Profit',
    value='$1,234.56',
    subtitle='Last 30 days',
    color='green',
    value_id='total-profit'
) }}
```

#### 2. Include-based Card (`card.html`)

For simpler use cases with include syntax:

```jinja2
{% include 'components/card.html' with {
    'icon': 'fas fa-wallet',
    'title': 'Total Portfolio Value',
    'value': '$0.00',
    'description': 'Loading...',
    'color': 'blue',
    'value_id': 'portfolio-value',
    'description_id': 'portfolio-change-text'
} %}
```

### Color Options

Available colors for the `color` parameter:
- `blue` - Blue gradient
- `green` - Green gradient  
- `red` - Red gradient
- `yellow` - Yellow-orange gradient
- `purple` - Purple gradient
- `indigo` - Indigo gradient
- `pink` - Pink gradient
- `gray` - Gray gradient

### Parameters

#### Common Parameters
- `icon` - FontAwesome icon class (default: 'fas fa-chart-line')
- `title` - Card title
- `color` - Color theme (default: 'blue')
- `extra_classes` - Additional CSS classes

#### stat_card Specific
- `value` - Display value
- `description` - Description text
- `value_id` - HTML ID for the value element
- `description_id` - HTML ID for the description element

#### feature_card Specific
- `description` - Feature description

#### info_card Specific
- `content` - Information content (can include HTML)

#### large_stat_card Specific
- `value` - Display value
- `subtitle` - Optional subtitle
- `value_id` - HTML ID for the value element

### Usage Examples

#### Dashboard Stats
```jinja2
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {{ stat_card(
        icon='fas fa-wallet',
        title='Portfolio Value',
        value='$10,000',
        description='+5.2% today',
        color='blue',
        value_id='portfolio-value'
    ) }}
    
    {{ stat_card(
        icon='fas fa-chart-line',
        title='Today\'s P&L',
        value='+$250',
        description='+2.5%',
        color='green',
        value_id='daily-pnl'
    ) }}
</div>
```

#### Feature Grid
```jinja2
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {{ feature_card(
        icon='fas fa-database',
        title='Data Ingestion',
        description='Real-time market data processing',
        color='green'
    ) }}
    
    {{ feature_card(
        icon='fas fa-cogs',
        title='Strategy Engine',
        description='Advanced trading algorithms',
        color='blue'
    ) }}
</div>
```

### Styling

All cards use consistent styling:
- White background with rounded corners
- Shadow effects with hover animations
- Gradient icon containers
- Responsive design
- Smooth transitions

The components automatically handle:
- Color theming
- Responsive layouts
- Hover effects
- Icon sizing and positioning
- Typography hierarchy

## Chart Features

### Professional Trading Charts

The Market Analysis page (`/analysis`) features professional-grade multi-pane trading charts built with Lightweight Charts library for optimal performance and professional appearance.

#### Chart Panels

1. **Price Chart (400px height)**
   - Candlestick chart with green (up) and red (down) bars
   - Simple Moving Average 20 (blue line)
   - Simple Moving Average 50 (red line)
   - Professional OHLC data visualization

2. **Volume Chart (120px height)**
   - Color-coded volume bars matching price movement
   - Green bars for up days, red for down days
   - Semi-transparent overlay for better readability

3. **MACD Indicator (150px height)**
   - MACD line (blue) - difference between 12 and 26-period EMAs
   - Signal line (red) - 9-period EMA of MACD line
   - Histogram (green/red) - difference between MACD and signal lines
   - Professional technical analysis standard

4. **RSI Indicator (150px height)**
   - RSI line (blue) - 14-period Relative Strength Index
   - Overbought level at 70 (gray dashed line)
   - Oversold level at 30 (gray dashed line)
   - Momentum oscillator for trend analysis

#### Interactive Controls

- **Symbol Selection**: Dropdown with all available symbols from your database
- **Timeframe Buttons**: 1 Week, 1 Month, 3 Months, 6 Months, 1 Year
- **Theme Toggle**: Switch between Light and Dark chart themes
- **Live Info Bar**: Shows current symbol, price, change, volume, high, and low

#### Theme Options

**Light Theme (Default)**
- White chart backgrounds
- Light gray grid lines
- Dark text for readability
- Professional clean appearance

**Dark Theme**
- Dark blue-gray backgrounds (#131722)
- Darker grid lines
- Light text for contrast
- Professional trading platform appearance

Theme preference is automatically saved in browser localStorage.

#### Synchronization Features

- **Crosshair Sync**: Hover over any chart to see synchronized crosshairs across all panels
- **Zoom Sync**: Zoom and pan operations are synchronized across all charts
- **Time Range Sync**: Visible time ranges stay aligned across all panels
- **Data Consistency**: All charts show the same time period and data points

#### Technical Indicators

The system includes professional-grade technical indicator calculations:

- **Simple Moving Average (SMA)**: 20 and 50-period calculations
- **MACD**: 12, 26, 9 parameter configuration
- **RSI**: 14-period Relative Strength Index
- **Volume Analysis**: Color-coded volume visualization

All indicators are calculated client-side for real-time updates and optimal performance.