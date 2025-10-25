# Streamlit UI Overview

This guide covers the modern Streamlit multipage interface with session state management for the trading system.

## Features

- **Portfolio Management**: Real-time portfolio tracking and performance metrics
- **Market Analysis**: Interactive charts with technical indicators using Plotly
- **System Information**: Team details and system architecture
- **Settings**: User preferences and session state management
- **Session State**: Persistent data sharing across all pages
- **Modern UI**: Clean, professional Streamlit interface

## Streamlit Pages

### 1. Portfolio Page
Real-time portfolio tracking and performance metrics:
- **Portfolio Metrics**: Total value, daily change, and performance indicators
- **Performance Charts**: Interactive charts showing portfolio performance over time
- **Asset Allocation**: Visual breakdown of portfolio holdings
- **Recent Activity**: Latest trades and transactions
- **Risk Metrics**: Portfolio risk indicators and exposure

### 2. Analysis Page
Interactive market analysis with technical indicators:
- **Symbol Selection**: Choose from available trading symbols
- **Price Charts**: Interactive Plotly charts with candlesticks and volume
- **Technical Indicators**: Moving averages, RSI, MACD, and other indicators
- **Volume Analysis**: Trading volume visualization
- **Session State**: Selected symbol and timeframe persist across page navigation

### 3. Author Page
System information and team details:
- **System Overview**: Trading system features and capabilities
- **Technology Stack**: Detailed technology information
- **Architecture**: System architecture and design
- **Development Team**: Team information and contact details
- **Session State Display**: Current session state information for debugging

### 4. Settings Page
User preferences and system configuration:
- **User Preferences**: Interface and display settings
- **Portfolio Settings**: Portfolio configuration options
- **Trading Parameters**: Trading-related settings
- **Session State Management**: Reset, clear, and export session state
- **System Configuration**: Application settings and preferences

## Session State Management

### Overview

The Streamlit UI uses session state to maintain data persistence across different pages, allowing for seamless navigation and data sharing.

### Features

#### Persistent Data
- **Selected Symbol**: Maintains selected trading symbol across pages
- **Timeframe**: Preserves selected chart timeframe
- **User Preferences**: Stores user interface settings
- **Portfolio Data**: Caches portfolio information for performance

#### State Management
- **Automatic Initialization**: Session state is initialized on app startup
- **Cross-Page Sharing**: Data persists when navigating between pages
- **State Updates**: Pages can modify session state variables
- **State Debugging**: Settings page shows current session state

### Usage

1. **Navigate Between Pages**: Use the sidebar navigation to switch pages
2. **Data Persistence**: Selected symbols and settings are maintained
3. **State Management**: Use the Settings page to manage session state
4. **Debug Information**: View current session state in the Author page

### Technical Implementation

#### Session State Variables
- `selected_symbol`: Currently selected trading symbol
- `timeframe`: Selected chart timeframe
- `portfolio_data`: Cached portfolio information
- `user_preferences`: User interface settings

#### State Operations
- **Initialize**: Set default values on app startup
- **Update**: Modify values from any page
- **Reset**: Clear all session state
- **Export**: View current state for debugging

## Streamlit Components

This section covers the Streamlit components and styling used throughout the application.

### Available Components

#### 1. Metrics Display
```python
import streamlit as st

# Display key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Portfolio Value", "$10,000", "+5.2%")
with col2:
    st.metric("Daily P&L", "+$250", "+2.5%")
with col3:
    st.metric("Total Return", "$1,234", "+12.3%")
with col4:
    st.metric("Sharpe Ratio", "1.85", "+0.15")
```

#### 2. Interactive Charts
```python
import plotly.graph_objects as go

# Create interactive charts
fig = go.Figure(data=go.Candlestick(
    x=df['date'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close']
))
st.plotly_chart(fig, use_container_width=True)
```

#### 3. Session State Management
```python
# Initialize session state
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = 'AAPL'

# Update session state
symbol = st.selectbox('Select Symbol', ['AAPL', 'MSFT', 'GOOGL'])
st.session_state.selected_symbol = symbol
```

#### 4. Data Display
```python
# Display data tables
st.dataframe(df, use_container_width=True)

# Display JSON data
st.json(session_state_data)

# Display code
st.code("""
def calculate_returns(prices):
    return prices.pct_change()
""", language='python')
```

### Custom Styling

#### CSS Customization
```python
# Load custom CSS
def load_css():
    with open("streamlit_ui/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
```

#### Theme Configuration
```python
# Configure page
st.set_page_config(
    page_title="Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### Layout Components

#### Sidebar Navigation
```python
# Sidebar navigation
with st.sidebar:
    st.title("Trading System")
    page = st.selectbox("Navigate", ["Portfolio", "Analysis", "Settings"])
```

#### Columns Layout
```python
# Multi-column layout
col1, col2 = st.columns([2, 1])
with col1:
    st.plotly_chart(chart)
with col2:
    st.metric("Price", "$150.25")
```

#### Tabs
```python
# Tabbed interface
tab1, tab2, tab3 = st.tabs(["Overview", "Charts", "Settings"])
with tab1:
    st.write("Portfolio overview")
with tab2:
    st.plotly_chart(chart)
with tab3:
    st.write("Settings")
```

### Interactive Elements

#### Form Controls
```python
# Form for user input
with st.form("trading_form"):
    symbol = st.text_input("Symbol")
    quantity = st.number_input("Quantity")
    submitted = st.form_submit_button("Place Order")
    
    if submitted:
        st.success(f"Order placed for {quantity} shares of {symbol}")
```

#### File Upload
```python
# File upload
uploaded_file = st.file_uploader("Upload CSV", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)
```

### Performance Optimization

#### Caching
```python
@st.cache_data
def load_market_data(symbol):
    # Expensive data loading operation
    return data

@st.cache_resource
def get_database_connection():
    # Database connection
    return connection
```

#### Session State Best Practices
```python
# Initialize once
if 'data' not in st.session_state:
    st.session_state.data = load_expensive_data()

# Use cached data
st.write(st.session_state.data)
```

## Chart Features

### Interactive Financial Charts

The Analysis page features interactive financial charts built with Plotly for professional visualization and analysis.

#### Chart Types

1. **Candlestick Charts**
   - Professional OHLC data visualization
   - Green (up) and red (down) candlesticks
   - Interactive hover with detailed information
   - Zoom and pan functionality

2. **Line Charts**
   - Moving averages and trend lines
   - Multiple series on same chart
   - Customizable colors and styles
   - Interactive legend and toggles

3. **Volume Charts**
   - Color-coded volume bars
   - Green for up days, red for down days
   - Volume analysis and patterns
   - Synchronized with price charts

#### Interactive Features

- **Symbol Selection**: Dropdown with available trading symbols
- **Timeframe Selection**: Choose from multiple time periods
- **Interactive Hover**: Detailed information on hover
- **Zoom and Pan**: Navigate through historical data
- **Legend Toggle**: Show/hide chart series
- **Download Options**: Export charts as images

#### Technical Indicators

The system includes comprehensive technical analysis:

- **Moving Averages**: SMA, EMA with customizable periods
- **MACD**: Moving Average Convergence Divergence
- **RSI**: Relative Strength Index
- **Bollinger Bands**: Price volatility indicators
- **Volume Analysis**: Trading volume patterns

#### Chart Customization

- **Color Themes**: Light and dark mode support
- **Chart Sizes**: Responsive design for different screen sizes
- **Interactive Elements**: Hover, click, and selection events
- **Export Options**: Save charts as PNG, SVG, or PDF

#### Performance Features

- **Data Caching**: Efficient data loading and caching
- **Session State**: Persistent chart settings across navigation
- **Real-time Updates**: Live data integration capabilities
- **Responsive Design**: Optimized for desktop and mobile