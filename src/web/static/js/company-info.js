/**
 * Company Info Management
 */

class CompanyInfoManager {
    constructor() {
        this.currentSymbol = null;
        this.init();
    }

    /**
     * Initialize the manager
     */
    init() {
        this.setupSymbolListener();
        this.loadInitialData();
    }

    /**
     * Setup listener for symbol changes from the symbol selector
     */
    setupSymbolListener() {
        const symbolSelect = document.getElementById('symbolSelect');
        if (symbolSelect) {
            symbolSelect.addEventListener('change', (e) => {
                this.currentSymbol = e.target.value;
                if (this.currentSymbol) {
                    this.loadCompanyInfo();
                }
            });
        }
    }

    /**
     * Load initial data when first symbol is selected
     */
    loadInitialData() {
        // Wait for dashboard to load first symbol
        const checkInterval = setInterval(() => {
            const symbolSelect = document.getElementById('symbolSelect');
            if (symbolSelect && symbolSelect.value && symbolSelect.value !== '') {
                this.currentSymbol = symbolSelect.value;
                this.loadCompanyInfo();
                clearInterval(checkInterval);
            }
        }, 500);

        // Clear interval after 5 seconds if no symbol found
        setTimeout(() => clearInterval(checkInterval), 5000);
    }

    /**
     * Load company information from API
     */
    async loadCompanyInfo() {
        if (!this.currentSymbol) {
            console.warn('No symbol selected');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch(`/api/company-info/${this.currentSymbol}`);

            if (!response.ok) {
                if (response.status === 404) {
                    this.showNoData();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }

            const data = await response.json();
            this.displayCompanyInfo(data);

        } catch (error) {
            console.error('Error loading company info:', error);
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Display company information
     */
    displayCompanyInfo(data) {
        // Header
        this.setTextContent('companyName', data.name || data.symbol);
        this.setTextContent('companySymbol', data.symbol);
        this.setTextContent('companyExchange', data.exchange || 'N/A');
        this.setTextContent('companyQuoteType', data.quote_type || 'N/A');
        
        // Exchange Card (separate from badge)
        this.setTextContent('companyExchangeCard', data.exchange || 'N/A');

        // Business Information
        this.setTextContent('companySector', data.sector || 'N/A');
        this.setTextContent('companyIndustry', data.industry || 'N/A');
        this.setTextContent('companyEmployees', data.employees ? data.employees.toLocaleString() : 'N/A');

        // Financial Metrics
        this.setTextContent('companyMarketCap', this.formatMarketCap(data.market_cap_billions));
        this.setTextContent('companyCurrency', data.currency || 'N/A');

        // Contact Information
        if (data.website) {
            const websiteElement = document.getElementById('companyWebsite');
            websiteElement.innerHTML = `<a href="${data.website}" target="_blank" style="color: #3b82f6; text-decoration: none;">${this.getDomain(data.website)}</a>`;
        } else {
            this.setTextContent('companyWebsite', 'N/A');
        }
        this.setTextContent('companyPhone', data.phone || 'N/A');

        // Location
        this.setTextContent('companyAddress', data.address || 'N/A');
        this.setTextContent('companyCity', data.city || 'N/A');
        this.setTextContent('companyCountry', data.country || 'N/A');

        // Description
        this.setTextContent('companyDescription', data.description || 'No description available.');

        // Show content
        document.getElementById('companyInfoContent').style.display = 'block';
    }

    /**
     * Format market cap
     */
    formatMarketCap(billions) {
        if (!billions) return 'N/A';
        if (billions >= 1000) {
            return `$${(billions / 1000).toFixed(2)}T`;
        } else if (billions >= 1) {
            return `$${billions.toFixed(2)}B`;
        } else {
            return `$${(billions * 1000).toFixed(2)}M`;
        }
    }

    /**
     * Extract domain from URL
     */
    getDomain(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.replace('www.', '');
        } catch {
            return url;
        }
    }

    /**
     * Set text content safely
     */
    setTextContent(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    }

    /**
     * Show/hide loading indicator
     */
    showLoading(show) {
        const loading = document.getElementById('companyLoading');
        const content = document.getElementById('companyInfoContent');
        
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
        if (content) {
            content.style.display = show ? 'none' : 'block';
        }
    }

    /**
     * Show no data message
     */
    showNoData() {
        const content = document.getElementById('companyInfoContent');
        if (content) {
            content.innerHTML = `
                <div class="loading-company">
                    <i class="fas fa-building" style="color: #94a3b8;"></i>
                    <p>No company information available for ${this.currentSymbol}</p>
                    <p style="font-size: 14px; color: #94a3b8; margin-top: 10px;">
                        Company data may not be available for all symbols.
                    </p>
                </div>
            `;
            content.style.display = 'block';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const content = document.getElementById('companyInfoContent');
        if (content) {
            content.innerHTML = `
                <div class="loading-company">
                    <i class="fas fa-exclamation-circle" style="color: #ef4444;"></i>
                    <p style="color: #ef4444;">Failed to load company information</p>
                    <p style="font-size: 14px; color: #64748b; margin-top: 10px;">
                        ${message}
                    </p>
                </div>
            `;
            content.style.display = 'block';
        }
    }
}

// Initialize company info manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('CompanyInfo: Initializing CompanyInfoManager');
    window.companyInfoManager = new CompanyInfoManager();
    console.log('CompanyInfo: Manager initialized and ready');
});

