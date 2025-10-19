/**
 * Professional Trading Charts Dashboard
 * Multi-pane synchronized charts with Lightweight Charts library
 */

class TradingChartsDashboard {
    constructor() {
        this.charts = {};
        this.series = {};
        this.currentSymbol = null;
        this.currentDays = 90;
        this.currentSource = 'polygon';  // Default to polygon to match dropdown default
        this.rawData = null;
        
        this.init();
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        this.setupEventListeners();
        // Don't load symbols here - let filters.js handle it
        // The filters manager will populate the dropdown and trigger change events
        console.log('Charts: Initialized, waiting for filters to load symbols');
    }

    /**
     * Setup event listeners for controls
     */
    setupEventListeners() {
        // Symbol selector
        const symbolSelect = document.getElementById('symbolSelect');
        if (symbolSelect) {
            symbolSelect.addEventListener('change', (e) => {
                console.log('Charts: Symbol change event received');
                console.log('Charts: e.target:', e.target);
                console.log('Charts: e.target.value:', e.target.value);
                console.log('Charts: typeof e.target.value:', typeof e.target.value);
                
                this.currentSymbol = e.target.value;
                console.log('Charts: this.currentSymbol set to:', this.currentSymbol);
                console.log('Charts: typeof this.currentSymbol:', typeof this.currentSymbol);
                
                if (this.currentSymbol && this.currentSymbol !== '[object Object]') {
                    this.loadChartData();
                } else if (this.currentSymbol === '[object Object]') {
                    console.error('Charts: ERROR - currentSymbol is "[object Object]"!');
                    console.error('Charts: symbolSelect value:', symbolSelect.value);
                    console.error('Charts: symbolSelect selectedIndex:', symbolSelect.selectedIndex);
                    if (symbolSelect.selectedIndex >= 0) {
                        const selectedOption = symbolSelect.options[symbolSelect.selectedIndex];
                        console.error('Charts: selected option:', selectedOption);
                        console.error('Charts: selected option value:', selectedOption.value);
                        console.error('Charts: selected option text:', selectedOption.text);
                    }
                }
            });
            console.log('Charts: Event listener registered for symbolSelect');
        } else {
            console.error('Charts: symbolSelect element not found!');
        }

        // Data source selector
        document.getElementById('sourceSelect').addEventListener('change', (e) => {
            this.currentSource = e.target.value || null;
            if (this.currentSymbol) {
                this.loadChartData();
            }
        });

        // Timeframe buttons
        document.querySelectorAll('.timeframe-buttons .btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.timeframe-buttons .btn').forEach(b => {
                    b.classList.remove('active');
                });
                e.target.classList.add('active');
                this.currentDays = parseInt(e.target.dataset.days);
                if (this.currentSymbol) {
                    this.loadChartData();
                }
            });
        });
    }

    /**
     * Load available symbols from API
     */
    async loadSymbols() {
        try {
            const response = await fetch('/api/market-data/symbols');
            const symbols = await response.json();
            
            const select = document.getElementById('symbolSelect');
            select.innerHTML = '<option value="">Select a symbol...</option>';
            
            symbols.forEach(symbol => {
                const option = document.createElement('option');
                option.value = symbol.symbol;
                option.textContent = `${symbol.symbol} ${symbol.name ? '- ' + symbol.name : ''} (${symbol.record_count} records)`;
                select.appendChild(option);
            });

            // Auto-select first symbol with data
            if (symbols.length > 0) {
                select.value = symbols[0].symbol;
                this.currentSymbol = symbols[0].symbol;
                this.loadChartData();
            }
        } catch (error) {
            console.error('Error loading symbols:', error);
            this.showError('Failed to load symbols');
        }
    }

    /**
     * Load chart data for current symbol
     */
    async loadChartData() {
        if (!this.currentSymbol) {
            console.warn('No symbol selected');
            return;
        }

        // Check if technical analysis tab is visible
        const tab = document.getElementById('technical-analysis-tab');
        if (tab) {
            const isVisible = tab.classList.contains('active');
            console.log('Technical analysis tab visible:', isVisible);
            if (!isVisible) {
                console.warn('Tab not visible, but will render charts anyway');
            }
        }

        this.showLoading(true);
        
        try {
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - this.currentDays);
            
            let url = `/api/market-data/data/${this.currentSymbol}?` +
                `limit=5000&` +
                `start_date=${startDate.toISOString()}&` +
                `end_date=${endDate.toISOString()}`;
            
            // Add data source filter if selected
            if (this.currentSource) {
                url += `&data_source=${this.currentSource}`;
            }
            
            console.log('Fetching data from:', url);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log(`Loaded ${data.length} data points for ${this.currentSymbol}`);
            
            // Data comes in descending order, reverse it
            this.rawData = data.reverse();
            
            if (this.rawData.length === 0) {
                this.showError(`No data available for ${this.currentSymbol} in the last ${this.currentDays} days. Try a different symbol or timeframe.`);
                return;
            }
            
            this.updateInfoBar();
            this.initializeCharts();
            this.renderCharts();
            
        } catch (error) {
            console.error('Error loading chart data:', error);
            this.showError(`Failed to load chart data: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Update info bar with latest data
     */
    updateInfoBar() {
        if (!this.rawData || this.rawData.length === 0) return;
        
        const latest = this.rawData[this.rawData.length - 1];
        const previous = this.rawData.length > 1 ? this.rawData[this.rawData.length - 2] : latest;
        
        const priceChange = latest.close - previous.close;
        const priceChangePercent = (priceChange / previous.close) * 100;
        
        document.getElementById('infoSymbol').textContent = this.currentSymbol;
        
        // Update data source badge
        const sourceBadge = document.getElementById('sourceBadge');
        const dataSource = latest.data_source || 'unknown';
        sourceBadge.textContent = dataSource.toUpperCase();
        sourceBadge.className = `source-badge ${dataSource}`;
        
        document.getElementById('infoPrice').textContent = TechnicalIndicators.formatPrice(latest.close);
        
        const changeElement = document.getElementById('infoChange');
        changeElement.textContent = `${priceChange >= 0 ? '+' : ''}${TechnicalIndicators.formatPrice(priceChange)} (${priceChangePercent.toFixed(2)}%)`;
        changeElement.className = `info-value ${priceChange >= 0 ? 'positive' : 'negative'}`;
        
        document.getElementById('infoVolume').textContent = TechnicalIndicators.formatVolume(latest.volume || 0);
        document.getElementById('infoHigh').textContent = TechnicalIndicators.formatPrice(latest.high);
        document.getElementById('infoLow').textContent = TechnicalIndicators.formatPrice(latest.low);
        
        document.getElementById('infoBar').style.display = 'flex';
    }

    /**
     * Initialize all chart instances
     */
    initializeCharts() {
        // Check if LightweightCharts is available
        if (typeof LightweightCharts === 'undefined') {
            console.error('LightweightCharts library not loaded');
            this.showError('Chart library not loaded. Please reload the page.');
            return;
        }

        // Clear existing charts
        Object.values(this.charts).forEach(chart => {
            try {
                chart.remove();
            } catch (e) {
                console.warn('Error removing chart:', e);
            }
        });
        this.charts = {};
        this.series = {};

        // Check if chart containers exist
        const priceChartEl = document.getElementById('priceChart');
        const volumeChartEl = document.getElementById('volumeChart');
        const macdChartEl = document.getElementById('macdChart');
        const rsiChartEl = document.getElementById('rsiChart');

        if (!priceChartEl || !volumeChartEl || !macdChartEl || !rsiChartEl) {
            console.error('Chart container elements not found');
            this.showError('Chart containers not found. Please reload the page.');
            return;
        }

        // Check container dimensions
        console.log('Chart container dimensions:');
        console.log('  priceChart:', priceChartEl.offsetWidth, 'x', priceChartEl.offsetHeight);
        console.log('  volumeChart:', volumeChartEl.offsetWidth, 'x', volumeChartEl.offsetHeight);
        console.log('  macdChart:', macdChartEl.offsetWidth, 'x', macdChartEl.offsetHeight);
        console.log('  rsiChart:', rsiChartEl.offsetWidth, 'x', rsiChartEl.offsetHeight);

        const chartOptions = this.getChartThemeOptions();

        // Price Chart
        this.charts.price = LightweightCharts.createChart(
            priceChartEl,
            { ...chartOptions, height: 400 }
        );
        this.series.candlestick = this.charts.price.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderUpColor: '#26a69a',
            borderDownColor: '#ef5350',
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        // Add moving averages to price chart
        this.series.sma20 = this.charts.price.addLineSeries({
            color: '#2962ff',
            lineWidth: 2,
            title: 'SMA 20',
        });
        this.series.sma50 = this.charts.price.addLineSeries({
            color: '#f23645',
            lineWidth: 2,
            title: 'SMA 50',
        });

        // Volume Chart
        this.charts.volume = LightweightCharts.createChart(
            volumeChartEl,
            { ...chartOptions, height: 120 }
        );
        this.series.volume = this.charts.volume.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
        });

        // MACD Chart
        this.charts.macd = LightweightCharts.createChart(
            macdChartEl,
            { ...chartOptions, height: 150 }
        );
        this.series.macdLine = this.charts.macd.addLineSeries({
            color: '#2962ff',
            lineWidth: 2,
            title: 'MACD',
        });
        this.series.signalLine = this.charts.macd.addLineSeries({
            color: '#f23645',
            lineWidth: 2,
            title: 'Signal',
        });
        this.series.macdHistogram = this.charts.macd.addHistogramSeries({
            color: '#26a69a',
            title: 'Histogram',
        });

        // RSI Chart
        this.charts.rsi = LightweightCharts.createChart(
            rsiChartEl,
            { ...chartOptions, height: 150 }
        );
        this.series.rsi = this.charts.rsi.addLineSeries({
            color: '#2962ff',
            lineWidth: 2,
            title: 'RSI',
        });

        // Add RSI reference lines
        this.series.rsiUpper = this.charts.rsi.addLineSeries({
            color: '#787b86',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            title: 'Overbought (70)',
        });
        this.series.rsiLower = this.charts.rsi.addLineSeries({
            color: '#787b86',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            title: 'Oversold (30)',
        });

        // Note: Synchronization will be enabled after first data render
        console.log('Charts initialized successfully');
    }

    /**
     * Synchronize crosshair movement across all charts
     */
    synchronizeCharts() {
        const charts = Object.values(this.charts);
        
        charts.forEach((chart, index) => {
            chart.subscribeCrosshairMove((param) => {
                if (!param || !param.time) {
                    return;
                }
                
                charts.forEach((otherChart, otherIndex) => {
                    if (index !== otherIndex) {
                        otherChart.setCrosshairPosition(0, param.time, otherChart.series()[0]);
                    }
                });
            });
        });

        // Synchronize visible time range
        const syncTimeScale = (sourceChart) => {
            const timeScale = sourceChart.timeScale();
            timeScale.subscribeVisibleTimeRangeChange(() => {
                const visibleRange = timeScale.getVisibleRange();
                if (visibleRange && visibleRange.from !== null && visibleRange.to !== null) {
                    charts.forEach(chart => {
                        if (chart !== sourceChart) {
                            try {
                                chart.timeScale().setVisibleRange(visibleRange);
                            } catch (e) {
                                // Ignore errors during synchronization
                                console.debug('Error syncing chart range:', e);
                            }
                        }
                    });
                }
            });
        };

        charts.forEach(syncTimeScale);
    }

    /**
     * Render all chart data
     */
    renderCharts() {
        if (!this.rawData || this.rawData.length === 0) {
            console.error('No data to render');
            return;
        }

        // Check if charts were initialized properly
        if (!this.charts.price || !this.charts.volume || !this.charts.macd || !this.charts.rsi) {
            console.error('Charts not properly initialized, skipping render');
            this.showError('Charts not properly initialized. Please reload the page.');
            return;
        }

        console.log('Rendering charts with', this.rawData.length, 'data points');

        // Prepare data
        const candlestickData = [];
        const volumeData = [];
        const closePrices = [];
        const timestamps = [];

        this.rawData.forEach(item => {
            // Validate data
            if (!item.timestamp || item.open == null || item.high == null || 
                item.low == null || item.close == null) {
                console.warn('Skipping invalid data point:', item);
                return;
            }

            const time = new Date(item.timestamp).getTime() / 1000; // Convert to seconds
            
            // Validate numeric values
            const open = parseFloat(item.open);
            const high = parseFloat(item.high);
            const low = parseFloat(item.low);
            const close = parseFloat(item.close);
            
            if (isNaN(open) || isNaN(high) || isNaN(low) || isNaN(close)) {
                console.warn('Skipping data with invalid prices:', item);
                return;
            }

            candlestickData.push({
                time: time,
                open: open,
                high: high,
                low: low,
                close: close,
            });

            volumeData.push({
                time: time,
                value: item.volume || 0,
                color: close >= open ? '#26a69a80' : '#ef535080',
            });

            closePrices.push(close);
            timestamps.push(time);
        });

        if (candlestickData.length === 0) {
            this.showError('No valid data points to display');
            return;
        }

        console.log('Valid data points:', candlestickData.length);

        // Set candlestick and volume data (with safety checks)
        if (this.series.candlestick) {
            this.series.candlestick.setData(candlestickData);
        } else {
            console.error('Candlestick series not initialized');
        }
        
        if (this.series.volume) {
            this.series.volume.setData(volumeData);
        } else {
            console.error('Volume series not initialized');
        }

        // Calculate and set moving averages
        const sma20 = TechnicalIndicators.SMA(closePrices, 20);
        const sma50 = TechnicalIndicators.SMA(closePrices, 50);

        if (this.series.sma20) {
            this.series.sma20.setData(
                sma20.map((value, index) => ({
                    time: timestamps[index],
                    value: value,
                })).filter(item => item.value !== null)
            );
        }

        if (this.series.sma50) {
            this.series.sma50.setData(
                sma50.map((value, index) => ({
                    time: timestamps[index],
                    value: value,
                })).filter(item => item.value !== null)
            );
        }

        // Calculate and set MACD
        const macd = TechnicalIndicators.MACD(closePrices, 12, 26, 9);
        
        if (this.series.macdLine) {
            this.series.macdLine.setData(
                macd.macd.map((value, index) => ({
                    time: timestamps[index],
                    value: value,
                })).filter(item => item.value !== null)
            );
        }

        if (this.series.signalLine) {
            this.series.signalLine.setData(
                macd.signal.map((value, index) => ({
                    time: timestamps[index],
                    value: value,
                })).filter(item => item.value !== null)
            );
        }

        if (this.series.macdHistogram) {
            this.series.macdHistogram.setData(
                macd.histogram.map((value, index) => ({
                    time: timestamps[index],
                    value: value,
                    color: value >= 0 ? '#26a69a80' : '#ef535080',
                })).filter(item => item.value !== null)
            );
        }

        // Calculate and set RSI
        const rsi = TechnicalIndicators.RSI(closePrices, 14);
        
        if (this.series.rsi) {
            this.series.rsi.setData(
                rsi.map((value, index) => ({
                    time: timestamps[index],
                    value: value,
                })).filter(item => item.value !== null)
            );
        }

        // Set RSI reference lines
        const rsiTimes = rsi
            .map((value, index) => timestamps[index])
            .filter((_, index) => rsi[index] !== null);

        if (rsiTimes.length > 0) {
            if (this.series.rsiUpper) {
                this.series.rsiUpper.setData([
                    { time: rsiTimes[0], value: 70 },
                    { time: rsiTimes[rsiTimes.length - 1], value: 70 },
                ]);
            }

            if (this.series.rsiLower) {
                this.series.rsiLower.setData([
                    { time: rsiTimes[0], value: 30 },
                    { time: rsiTimes[rsiTimes.length - 1], value: 30 },
                ]);
            }
        }

        // Fit content for all charts
        console.log('Fitting content for all charts');
        Object.values(this.charts).forEach(chart => {
            try {
                chart.timeScale().fitContent();
            } catch (e) {
                console.error('Error fitting chart content:', e);
            }
        });

        // Enable chart synchronization
        setTimeout(() => {
            this.synchronizeCharts();
            console.log('Chart synchronization enabled');
        }, 100);

        console.log('Charts rendered successfully');
    }

    /**
     * Get chart theme options based on current theme
     */
    getChartThemeOptions() {
        // Check if we're in dark mode by looking at the container class
        const isDark = document.querySelector('.charts-container').classList.contains('dark-theme');
        
        if (isDark) {
            return {
                layout: {
                    background: { color: '#131722' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: '#1e222d' },
                    horzLines: { color: '#1e222d' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: {
                        color: '#758696',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                    },
                    horzLine: {
                        color: '#758696',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                    },
                },
                timeScale: {
                    borderColor: '#2a2e39',
                    timeVisible: true,
                    secondsVisible: false,
                },
                rightPriceScale: {
                    borderColor: '#2a2e39',
                },
            };
        } else {
            return {
                layout: {
                    background: { color: '#ffffff' },
                    textColor: '#191919',
                },
                grid: {
                    vertLines: { color: '#f0f0f0' },
                    horzLines: { color: '#f0f0f0' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: {
                        color: '#758696',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                    },
                    horzLine: {
                        color: '#758696',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                    },
                },
                timeScale: {
                    borderColor: '#e0e0e0',
                    timeVisible: true,
                    secondsVisible: false,
                },
                rightPriceScale: {
                    borderColor: '#e0e0e0',
                },
            };
        }
    }

    /**
     * Resize and refit all charts (useful when container visibility changes)
     */
    resizeCharts() {
        if (!this.charts || Object.keys(this.charts).length === 0) {
            console.log('No charts to resize');
            return;
        }

        console.log('Resizing all charts');
        Object.values(this.charts).forEach(chart => {
            try {
                chart.resize();
                chart.timeScale().fitContent();
            } catch (e) {
                console.warn('Error resizing chart:', e);
            }
        });
    }

    /**
     * Update chart theme
     */
    updateChartTheme(theme) {
        if (!this.charts || Object.keys(this.charts).length === 0) {
            console.log('Charts not initialized yet, skipping theme update');
            return;
        }

        console.log('Updating chart theme to:', theme);
        
        // Store current data and visible ranges before recreating charts
        const currentData = this.rawData;
        const visibleRanges = {};
        
        // Store visible ranges for each chart
        Object.entries(this.charts).forEach(([name, chart]) => {
            try {
                visibleRanges[name] = chart.timeScale().getVisibleRange();
            } catch (e) {
                console.warn(`Could not get visible range for ${name}:`, e);
            }
        });

        // Reinitialize charts with new theme
        this.initializeCharts();
        
        // Restore data and visible ranges
        if (currentData && currentData.length > 0) {
            this.rawData = currentData;
            this.renderCharts();
            
            // Restore visible ranges after a short delay to ensure charts are ready
            setTimeout(() => {
                Object.entries(visibleRanges).forEach(([name, range]) => {
                    if (this.charts[name] && range) {
                        try {
                            this.charts[name].timeScale().setVisibleRange(range);
                        } catch (e) {
                            console.warn(`Could not restore visible range for ${name}:`, e);
                        }
                    }
                });
            }, 100);
        }
    }

    /**
     * Show/hide loading indicator
     */
    showLoading(show) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.classList.add('active');
        } else {
            loading.classList.remove('active');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        // Clear existing charts first
        Object.values(this.charts).forEach(chart => {
            try {
                chart.remove();
            } catch (e) {
                // Ignore errors when removing charts
            }
        });
        this.charts = {};
        this.series = {};
        
        const container = document.querySelector('.chart-container');
        container.innerHTML = `
            <div class="error-message">
                <h3>⚠️ Error</h3>
                <p>${message}</p>
                <button class="btn" onclick="location.reload()" style="margin-top: 15px;">
                    Reload Page
                </button>
            </div>
        `;
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Charts: Initializing TradingChartsDashboard');
    window.dashboard = new TradingChartsDashboard();
    console.log('Charts: Dashboard initialized and ready');
});

