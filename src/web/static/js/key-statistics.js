/**
 * Key Statistics Module
 * Handles loading and displaying fundamental metrics
 */

class KeyStatisticsManager {
    constructor() {
        this.currentSymbol = null;
        this.statsData = null;
    }

    /**
     * Load key statistics for a symbol
     */
    async loadKeyStatistics(symbol) {
        if (!symbol) {
            console.error('No symbol provided');
            return;
        }

        this.currentSymbol = symbol;
        
        // Show loading indicator
        document.getElementById('fundamentalsLoading').style.display = 'block';
        document.getElementById('fundamentalsContent').style.display = 'none';

        try {
            const response = await fetch(`/api/key-statistics/${symbol}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    this.showNoDataMessage(symbol);
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.statsData = data;
                this.displayKeyStatistics(data);
            } else {
                this.showErrorMessage('Failed to load key statistics');
            }

        } catch (error) {
            console.error('Error loading key statistics:', error);
            this.showErrorMessage(`Error: ${error.message}`);
        }
    }

    /**
     * Display key statistics in the UI
     */
    async displayKeyStatistics(data) {
        // Hide loading, show content
        document.getElementById('fundamentalsLoading').style.display = 'none';
        document.getElementById('fundamentalsContent').style.display = 'block';

        // Fetch company name from company info API
        try {
            const companyResponse = await fetch(`/api/company-info/${data.symbol}`);
            if (companyResponse.ok) {
                const companyData = await companyResponse.json();
                document.getElementById('fundCompanyName').textContent = companyData.name || data.symbol;
            } else {
                document.getElementById('fundCompanyName').textContent = data.symbol;
            }
        } catch (error) {
            document.getElementById('fundCompanyName').textContent = data.symbol;
        }

        // Header badges
        document.getElementById('fundSymbol').textContent = data.symbol;
        document.getElementById('fundDate').textContent = `As of: ${data.date}`;
        document.getElementById('fundSource').textContent = data.data_source.toUpperCase();

        const stats = data.data;

        // Large Market Cap Card
        this.setValue('fundMarketCapLarge', stats.valuation.market_cap_display);
        
        // Top Summary Cards
        this.setValue('fundPECard', this.formatNumber(stats.valuation.trailing_pe, 2));
        this.setValue('fundROECard', stats.profitability.roe_display);
        this.setValue('fundProfitMarginCard', stats.profitability.profit_margin_display);

        // Valuation Metrics
        this.setValue('fundMarketCap', stats.valuation.market_cap_display);
        this.setFormattedValue('fundEnterpriseValue', stats.valuation.enterprise_value);
        this.setValue('fundTrailingPE', this.formatNumber(stats.valuation.trailing_pe, 2));
        this.setValue('fundForwardPE', this.formatNumber(stats.valuation.forward_pe, 2));
        this.setValue('fundPEG', this.formatNumber(stats.valuation.peg_ratio, 2));
        this.setValue('fundPriceBook', this.formatNumber(stats.valuation.price_to_book, 2));
        this.setValue('fundPriceSales', this.formatNumber(stats.valuation.price_to_sales, 2));
        this.setValue('fundEVRevenue', this.formatNumber(stats.valuation.enterprise_to_revenue, 2));
        this.setValue('fundEVEBITDA', this.formatNumber(stats.valuation.enterprise_to_ebitda, 2));

        // Profitability Metrics
        this.setValue('fundProfitMargin', stats.profitability.profit_margin_display);
        this.setPercentage('fundOperatingMargin', stats.profitability.operating_margin);
        this.setPercentage('fundGrossMargin', stats.profitability.gross_margin);
        this.setPercentage('fundEBITDAMargin', stats.profitability.ebitda_margin);
        this.setValue('fundROE', stats.profitability.roe_display);
        this.setPercentage('fundROA', stats.profitability.return_on_assets);

        // Financial Health
        this.setFormattedValue('fundTotalCash', stats.financial_health.total_cash);
        this.setFormattedValue('fundTotalDebt', stats.financial_health.total_debt);
        this.setValue('fundDebtEquity', stats.financial_health.debt_to_equity_display);
        this.setValue('fundCurrentRatio', this.formatNumber(stats.financial_health.current_ratio, 2));
        this.setValue('fundQuickRatio', this.formatNumber(stats.financial_health.quick_ratio, 2));
        this.setFormattedValue('fundFCF', stats.financial_health.free_cash_flow);
        this.setFormattedValue('fundRevenue', stats.financial_health.revenue);
        this.setValue('fundEPS', stats.financial_health.earnings_per_share ? `$${stats.financial_health.earnings_per_share.toFixed(2)}` : 'N/A');

        // Growth Metrics
        this.setPercentage('fundRevenueGrowth', stats.growth.revenue_growth);
        this.setPercentage('fundEarningsGrowth', stats.growth.earnings_growth);

        // Trading Metrics
        this.setValue('fundBeta', this.formatNumber(stats.trading.beta, 2));
        this.setValue('fund52WHigh', stats.trading.fifty_two_week_high ? `$${stats.trading.fifty_two_week_high.toFixed(2)}` : 'N/A');
        this.setValue('fund52WLow', stats.trading.fifty_two_week_low ? `$${stats.trading.fifty_two_week_low.toFixed(2)}` : 'N/A');
        this.setValue('fund50DAvg', stats.trading.fifty_day_average ? `$${stats.trading.fifty_day_average.toFixed(2)}` : 'N/A');
        this.setValue('fund200DAvg', stats.trading.two_hundred_day_average ? `$${stats.trading.two_hundred_day_average.toFixed(2)}` : 'N/A');
        this.setFormattedVolume('fundAvgVolume', stats.trading.average_volume);

        // Dividends & Ownership
        this.setValue('fundDivYield', stats.dividends.dividend_yield_display);
        this.setValue('fundDivRate', stats.dividends.dividend_rate ? `$${stats.dividends.dividend_rate.toFixed(2)}` : 'N/A');
        this.setPercentage('fundPayoutRatio', stats.dividends.payout_ratio);
        this.setPercentage('fundInsiders', stats.shares.held_percent_insiders);
        this.setPercentage('fundInstitutional', stats.shares.held_percent_institutions);
        this.setFormattedVolume('fundShortInterest', stats.shares.shares_short);
    }

    /**
     * Set element value with fallback
     */
    setValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value || 'N/A';
        }
    }

    /**
     * Format percentage value
     */
    setPercentage(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            if (value !== null && value !== undefined) {
                element.textContent = `${(value * 100).toFixed(2)}%`;
            } else {
                element.textContent = 'N/A';
            }
        }
    }

    /**
     * Format large numbers with K/M/B/T suffixes
     */
    setFormattedValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            if (value !== null && value !== undefined) {
                element.textContent = this.formatLargeNumber(value);
            } else {
                element.textContent = 'N/A';
            }
        }
    }

    /**
     * Format volume with K/M/B suffixes
     */
    setFormattedVolume(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            if (value !== null && value !== undefined) {
                element.textContent = this.formatVolume(value);
            } else {
                element.textContent = 'N/A';
            }
        }
    }

    /**
     * Format number with specified decimals
     */
    formatNumber(value, decimals = 2) {
        if (value === null || value === undefined) {
            return 'N/A';
        }
        return value.toFixed(decimals);
    }

    /**
     * Format large numbers with suffixes
     */
    formatLargeNumber(value) {
        if (value === null || value === undefined) {
            return 'N/A';
        }

        const absValue = Math.abs(value);
        const sign = value < 0 ? '-' : '';

        if (absValue >= 1e12) {
            return `${sign}$${(absValue / 1e12).toFixed(2)}T`;
        } else if (absValue >= 1e9) {
            return `${sign}$${(absValue / 1e9).toFixed(2)}B`;
        } else if (absValue >= 1e6) {
            return `${sign}$${(absValue / 1e6).toFixed(2)}M`;
        } else if (absValue >= 1e3) {
            return `${sign}$${(absValue / 1e3).toFixed(2)}K`;
        } else {
            return `${sign}$${absValue.toFixed(2)}`;
        }
    }

    /**
     * Format volume numbers
     */
    formatVolume(value) {
        if (value === null || value === undefined) {
            return 'N/A';
        }

        if (value >= 1e9) {
            return `${(value / 1e9).toFixed(2)}B`;
        } else if (value >= 1e6) {
            return `${(value / 1e6).toFixed(2)}M`;
        } else if (value >= 1e3) {
            return `${(value / 1e3).toFixed(2)}K`;
        } else {
            return value.toLocaleString();
        }
    }

    /**
     * Show message when no data is available
     */
    showNoDataMessage(symbol) {
        document.getElementById('fundamentalsLoading').style.display = 'none';
        document.getElementById('fundamentalsContent').style.display = 'block';
        
        document.getElementById('fundCompanyName').textContent = symbol;
        document.getElementById('fundSymbol').textContent = symbol;
        document.getElementById('fundDate').textContent = 'No data available';
        document.getElementById('fundSource').textContent = 'Load data first';
    }

    /**
     * Show error message
     */
    showErrorMessage(message) {
        document.getElementById('fundamentalsLoading').innerHTML = `
            <i class="fas fa-exclamation-triangle" style="color: #dc2626;"></i>
            <p style="color: #dc2626;">${message}</p>
        `;
    }
}

// Initialize global instance
window.keyStatisticsManager = new KeyStatisticsManager();

// Hook into symbol change events
document.addEventListener('DOMContentLoaded', function() {
    // Listen for symbol selection changes
    const symbolSelect = document.getElementById('symbolSelect');
    if (symbolSelect) {
        symbolSelect.addEventListener('change', function() {
            const symbol = this.value;
            if (symbol && window.keyStatisticsManager) {
                // Load key statistics when fundamentals tab is active
                const fundamentalsTab = document.querySelector('[data-tab="fundamentals"]');
                if (fundamentalsTab && fundamentalsTab.classList.contains('active')) {
                    window.keyStatisticsManager.loadKeyStatistics(symbol);
                }
            }
        });
    }

    // Listen for tab clicks
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Load key statistics when fundamentals tab is clicked
            if (tabName === 'fundamentals') {
                const symbolSelect = document.getElementById('symbolSelect');
                const symbol = symbolSelect ? symbolSelect.value : null;
                
                if (symbol && window.keyStatisticsManager) {
                    window.keyStatisticsManager.loadKeyStatistics(symbol);
                }
            }
        });
    });
});

