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
Advanced market data analysis and visualization:
- **Interactive Charts**: Plotly.js charts for price analysis
- **Market Statistics**: Data availability and symbol information
- **OHLC Analysis**: Open, High, Low, Close data visualization
- **Performance Metrics**: Historical performance analysis

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