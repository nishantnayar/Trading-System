/**
 * Pairs Trading Strategy JavaScript
 * Handles real-time pair monitoring, chart rendering, and strategy management
 */

class PairsTradingManager {
    constructor() {
        this.charts = new Map();
        this.updateInterval = null;
        this.isStrategyActive = false;
        this.pairsData = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startRealTimeUpdates();
    }

    setupEventListeners() {
        // Configuration save
        document.getElementById('saveConfig')?.addEventListener('click', () => {
            this.saveConfiguration();
        });

        // Backtest run
        document.getElementById('runBacktest')?.addEventListener('click', () => {
            this.runBacktest();
        });

        // Real-time updates toggle
        document.getElementById('strategyToggle')?.addEventListener('click', () => {
            this.toggleStrategy();
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadPairsData(),
                this.loadPerformanceData(),
                this.loadConfiguration()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data');
        }
    }

    async loadPairsData() {
        try {
            const response = await fetch('/api/strategies/pairs/active');
            if (!response.ok) throw new Error('Failed to fetch pairs data');
            
            const data = await response.json();
            this.pairsData = data.pairs || [];
            this.renderPairsGrid();
        } catch (error) {
            console.error('Error loading pairs data:', error);
            this.showPairsError();
        }
    }

    async loadPerformanceData() {
        try {
            const response = await fetch('/api/strategies/pairs/performance');
            if (!response.ok) throw new Error('Failed to fetch performance data');
            
            const data = await response.json();
            this.updatePerformanceMetrics(data);
            this.updatePerformanceCharts(data);
        } catch (error) {
            console.error('Error loading performance data:', error);
        }
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/strategies/pairs/config');
            if (!response.ok) throw new Error('Failed to fetch configuration');
            
            const data = await response.json();
            this.populateConfigurationForm(data);
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }

    renderPairsGrid() {
        const grid = document.getElementById('pairsGrid');
        const loading = document.getElementById('pairsLoading');
        
        if (!grid || !loading) return;

        if (this.pairsData.length === 0) {
            loading.innerHTML = `
                <i class="fas fa-info-circle"></i>
                <p>No active pairs found. Configure pairs in the Configuration tab.</p>
            `;
            return;
        }
        
        loading.style.display = 'none';
        
        grid.innerHTML = this.pairsData.map(pair => this.createPairCard(pair)).join('');
        
        // Initialize charts for each pair
        this.pairsData.forEach(pair => {
            this.initializePairChart(pair);
        });
    }

    createPairCard(pair) {
        const statusClass = pair.status === 'active' ? 'active' : 'inactive';
        const zScoreClass = pair.zScore >= 0 ? 'positive' : 'negative';
        const pnlClass = pair.pnl >= 0 ? 'positive' : 'negative';
        
        return `
            <div class="pair-card" data-pair-id="${pair.id}">
                <div class="pair-header">
                    <div>
                        <div class="pair-name">${pair.name}</div>
                        <div class="pair-symbols">${pair.symbol1} / ${pair.symbol2}</div>
                    </div>
                    <div class="pair-status ${statusClass}">${pair.status}</div>
                </div>
                
                <div class="pair-metrics">
                    <div class="metric-item">
                        <div class="metric-label">Current Z-Score</div>
                        <div class="metric-value ${zScoreClass}">${pair.zScore.toFixed(2)}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">P&L</div>
                        <div class="metric-value ${pnlClass}">$${pair.pnl.toFixed(2)}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Correlation</div>
                        <div class="metric-value">${(pair.correlation * 100).toFixed(1)}%</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Days Held</div>
                        <div class="metric-value">${pair.daysHeld}</div>
                    </div>
                </div>
                
                <div class="pair-chart" id="chart-${pair.id}">
                    <!-- Chart will be rendered here -->
                </div>
                
                <div class="pair-actions">
                    <button class="action-btn primary" onclick="pairsManager.viewPairDetails('${pair.id}')">
                        <i class="fas fa-eye"></i> Details
                    </button>
                    <button class="action-btn" onclick="pairsManager.adjustPairParameters('${pair.id}')">
                        <i class="fas fa-cog"></i> Adjust
                    </button>
                    <button class="action-btn danger" onclick="pairsManager.closePair('${pair.id}')">
                        <i class="fas fa-times"></i> Close
                    </button>
                </div>
            </div>
        `;
    }

    initializePairChart(pair) {
        const chartContainer = document.getElementById(`chart-${pair.id}`);
        if (!chartContainer) return;

        try {
            // Create chart using Lightweight Charts
            const chart = LightweightCharts.createChart(chartContainer, {
                width: chartContainer.clientWidth,
                height: 120,
                layout: {
                    background: { color: 'white' },
                    textColor: '#333',
                },
                grid: {
                    vertLines: { color: '#f0f0f0' },
                    horzLines: { color: '#f0f0f0' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#e0e0e0',
                },
                timeScale: {
                    borderColor: '#e0e0e0',
                    timeVisible: true,
                    secondsVisible: false,
                },
            });

            // Add spread line
            const spreadSeries = chart.addLineSeries({
                color: '#3b82f6',
                lineWidth: 2,
                title: 'Spread',
            });

            // Add Z-score line
            const zScoreSeries = chart.addLineSeries({
                color: '#ef4444',
                lineWidth: 1,
                title: 'Z-Score',
            });

            // Add threshold lines
            const upperThreshold = chart.addLineSeries({
                color: '#10b981',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'Entry Threshold',
            });

            const lowerThreshold = chart.addLineSeries({
                color: '#10b981',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'Entry Threshold',
            });

            // Store chart reference
            this.charts.set(pair.id, {
                chart,
                spreadSeries,
                zScoreSeries,
                upperThreshold,
                lowerThreshold
            });

            // Load historical data for this pair
            this.loadPairHistoricalData(pair.id);

        } catch (error) {
            console.error(`Error initializing chart for pair ${pair.id}:`, error);
        }
    }

    async loadPairHistoricalData(pairId) {
        try {
            const response = await fetch(`/api/strategies/pairs/${pairId}/history`);
            if (!response.ok) throw new Error('Failed to fetch historical data');
            
            const data = await response.json();
            const chartData = this.charts.get(pairId);
            
            if (chartData && data.history) {
                // Convert data to chart format
                const spreadData = data.history.map(item => ({
                    time: item.timestamp / 1000, // Convert to seconds
                    value: item.spread
                }));

                const zScoreData = data.history.map(item => ({
                    time: item.timestamp / 1000,
                    value: item.zScore
                }));

                // Set data
                chartData.spreadSeries.setData(spreadData);
                chartData.zScoreSeries.setData(zScoreData);
                
                // Set threshold lines
                const entryThreshold = data.entryThreshold || 2.0;
                const exitThreshold = data.exitThreshold || 0.5;
                
                const upperThresholdData = spreadData.map(item => ({
                    time: item.time,
                    value: entryThreshold
                }));
                
                const lowerThresholdData = spreadData.map(item => ({
                    time: item.time,
                    value: -entryThreshold
                }));

                chartData.upperThreshold.setData(upperThresholdData);
                chartData.lowerThreshold.setData(lowerThresholdData);
            }
        } catch (error) {
            console.error(`Error loading historical data for pair ${pairId}:`, error);
        }
    }

    updatePerformanceMetrics(data) {
        const metrics = {
            totalPnl: document.getElementById('totalPnl'),
            sharpeRatio: document.getElementById('sharpeRatio'),
            maxDrawdown: document.getElementById('maxDrawdown'),
            winRate: document.getElementById('winRate'),
            activePairs: document.getElementById('activePairs'),
            avgHoldTime: document.getElementById('avgHoldTime')
        };

        if (metrics.totalPnl) metrics.totalPnl.textContent = `$${data.totalPnl?.toFixed(2) || '0.00'}`;
        if (metrics.sharpeRatio) metrics.sharpeRatio.textContent = data.sharpeRatio?.toFixed(2) || '0.00';
        if (metrics.maxDrawdown) metrics.maxDrawdown.textContent = `${data.maxDrawdown?.toFixed(1) || '0.0'}%`;
        if (metrics.winRate) metrics.winRate.textContent = `${data.winRate?.toFixed(1) || '0.0'}%`;
        if (metrics.activePairs) metrics.activePairs.textContent = data.activePairs || '0';
        if (metrics.avgHoldTime) metrics.avgHoldTime.textContent = `${data.avgHoldTime || '0'} days`;
    }

    updatePerformanceCharts(data) {
        // Update performance charts if they exist
        if (data.performanceHistory) {
            this.updateChart('performanceChart', data.performanceHistory);
        }
        
        if (data.drawdownHistory) {
            this.updateChart('drawdownChart', data.drawdownHistory);
        }
        
        if (data.monthlyReturns) {
            this.updateChart('monthlyReturnsChart', data.monthlyReturns);
        }
    }

    updateChart(chartId, data) {
        const chartElement = document.getElementById(chartId);
        if (!chartElement) return;

        // This would integrate with your existing chart system
        // For now, we'll just log the data
        console.log(`Updating chart ${chartId} with data:`, data);
    }

    populateConfigurationForm(config) {
        const formFields = {
            entryThreshold: document.getElementById('entryThreshold'),
            exitThreshold: document.getElementById('exitThreshold'),
            stopLossThreshold: document.getElementById('stopLossThreshold'),
            positionSize: document.getElementById('positionSize'),
            lookbackPeriod: document.getElementById('lookbackPeriod'),
            maxActivePairs: document.getElementById('maxActivePairs'),
            maxDrawdownLimit: document.getElementById('maxDrawdownLimit'),
            maxDailyLoss: document.getElementById('maxDailyLoss'),
            maxSectorExposure: document.getElementById('maxSectorExposure'),
            rebalanceFrequency: document.getElementById('rebalanceFrequency')
        };

        Object.entries(formFields).forEach(([key, element]) => {
            if (element && config[key] !== undefined) {
                element.value = config[key];
            }
        });
    }

    async saveConfiguration() {
        try {
            const config = {
                entryThreshold: parseFloat(document.getElementById('entryThreshold').value),
                exitThreshold: parseFloat(document.getElementById('exitThreshold').value),
                stopLossThreshold: parseFloat(document.getElementById('stopLossThreshold').value),
                positionSize: parseFloat(document.getElementById('positionSize').value),
                lookbackPeriod: parseInt(document.getElementById('lookbackPeriod').value),
                maxActivePairs: parseInt(document.getElementById('maxActivePairs').value),
                maxDrawdownLimit: parseFloat(document.getElementById('maxDrawdownLimit').value),
                maxDailyLoss: parseFloat(document.getElementById('maxDailyLoss').value),
                maxSectorExposure: parseFloat(document.getElementById('maxSectorExposure').value),
                rebalanceFrequency: document.getElementById('rebalanceFrequency').value
            };

            const response = await fetch('/api/strategies/pairs/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showSuccess('Configuration saved successfully');
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showError('Failed to save configuration');
        }
    }

    async runBacktest() {
        try {
            const backtestConfig = {
                startDate: document.getElementById('backtestStartDate').value,
                endDate: document.getElementById('backtestEndDate').value,
                initialCapital: parseFloat(document.getElementById('initialCapital').value),
                entryThreshold: parseFloat(document.getElementById('backtestEntryThreshold').value)
            };

            const response = await fetch('/api/strategies/pairs/backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(backtestConfig)
            });

            if (response.ok) {
                const results = await response.json();
                this.displayBacktestResults(results);
            } else {
                throw new Error('Failed to run backtest');
            }
        } catch (error) {
            console.error('Error running backtest:', error);
            this.showError('Failed to run backtest');
        }
    }

    displayBacktestResults(results) {
        const resultsDiv = document.getElementById('backtestResults');
        if (resultsDiv) {
            resultsDiv.style.display = 'block';
            // Update backtest chart with results
            this.updateChart('backtestChart', results.chartData);
        }
    }

    async toggleStrategy() {
        try {
            const isActive = this.isStrategyActive;
            const endpoint = isActive ? '/api/strategies/pairs/stop' : '/api/strategies/pairs/start';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.isStrategyActive = !isActive;
                this.updateStrategyToggle();
                this.loadPairsData(); // Refresh data
            } else {
                throw new Error(`Failed to ${isActive ? 'stop' : 'start'} strategy`);
            }
        } catch (error) {
            console.error('Error toggling strategy:', error);
            this.showError(`Failed to ${this.isStrategyActive ? 'stop' : 'start'} strategy`);
        }
    }

    updateStrategyToggle() {
        const toggle = document.getElementById('strategyToggle');
        if (!toggle) return;

        if (this.isStrategyActive) {
            toggle.classList.add('active');
            toggle.classList.remove('disabled');
            toggle.innerHTML = '<i class="fas fa-pause"></i><span>Stop Strategy</span>';
        } else {
            toggle.classList.remove('active');
            toggle.classList.add('disabled');
            toggle.innerHTML = '<i class="fas fa-play"></i><span>Start Strategy</span>';
        }
    }

    startRealTimeUpdates() {
        // Update data every 30 seconds
        this.updateInterval = setInterval(() => {
            if (this.isStrategyActive) {
                this.loadPairsData();
                this.loadPerformanceData();
            }
        }, 30000);
    }

    stopRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    // Pair management methods
    async viewPairDetails(pairId) {
        try {
            const response = await fetch(`/api/strategies/pairs/${pairId}/details`);
            if (response.ok) {
                const data = await response.json();
                this.showPairDetailsModal(data);
            }
        } catch (error) {
            console.error('Error loading pair details:', error);
            this.showError('Failed to load pair details');
        }
    }

    async adjustPairParameters(pairId) {
        try {
            const response = await fetch(`/api/strategies/pairs/${pairId}/config`);
            if (response.ok) {
                const data = await response.json();
                this.showPairConfigModal(pairId, data);
            }
        } catch (error) {
            console.error('Error loading pair configuration:', error);
            this.showError('Failed to load pair configuration');
        }
    }

    async closePair(pairId) {
        if (!confirm('Are you sure you want to close this pair position?')) {
            return;
        }

        try {
            const response = await fetch(`/api/strategies/pairs/${pairId}/close`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.showSuccess('Pair position closed successfully');
                this.loadPairsData(); // Refresh data
            } else {
                throw new Error('Failed to close pair position');
            }
        } catch (error) {
            console.error('Error closing pair:', error);
            this.showError('Failed to close pair position');
        }
    }

    // Utility methods
    showSuccess(message) {
        // Implement success notification
        console.log('Success:', message);
        // You can integrate with a toast notification system here
    }

    showError(message) {
        // Implement error notification
        console.error('Error:', message);
        // You can integrate with a toast notification system here
    }

    showPairsError() {
        const loading = document.getElementById('pairsLoading');
        if (loading) {
            loading.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load pairs data. Please try again.</p>
            `;
        }
    }

    showPairDetailsModal(data) {
        // Implement pair details modal
        console.log('Pair details:', data);
    }

    showPairConfigModal(pairId, config) {
        // Implement pair configuration modal
        console.log('Pair config for', pairId, ':', config);
    }

    // Cleanup method
    destroy() {
        this.stopRealTimeUpdates();
        this.charts.forEach(chart => {
            chart.chart.remove();
        });
        this.charts.clear();
    }
}

// Initialize the pairs trading manager when the page loads
let pairsManager;

document.addEventListener('DOMContentLoaded', function() {
    pairsManager = new PairsTradingManager();
});

// Cleanup when page unloads
window.addEventListener('beforeunload', function() {
    if (pairsManager) {
        pairsManager.destroy();
    }
});

// Export for global access
window.pairsManager = pairsManager;
