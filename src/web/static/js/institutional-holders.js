/**
 * Institutional Holders Module
 * Handles loading and displaying institutional ownership data
 */

class InstitutionalHoldersManager {
    constructor() {
        this.currentSymbol = null;
    }

    /**
     * Load institutional holders for a symbol
     */
    async loadInstitutionalHolders(symbol, limit = 10) {
        if (!symbol) {
            console.error('No symbol provided');
            return;
        }

        this.currentSymbol = symbol;
        
        // Show loading
        document.getElementById('institutionalHoldersLoading').style.display = 'block';
        document.getElementById('institutionalHoldersContent').style.display = 'none';
        document.getElementById('institutionalHoldersNoData').style.display = 'none';

        try {
            const response = await fetch(`/api/institutional-holders/${symbol}?limit=${limit}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success && data.count > 0) {
                this.displayInstitutionalHolders(data.holders);
            } else {
                this.showNoDataMessage();
            }

        } catch (error) {
            console.error('Error loading institutional holders:', error);
            this.showErrorMessage(`Error: ${error.message}`);
        }
    }

    /**
     * Display institutional holders in table
     */
    displayInstitutionalHolders(holders) {
        // Hide loading, show content
        document.getElementById('institutionalHoldersLoading').style.display = 'none';
        document.getElementById('institutionalHoldersContent').style.display = 'block';
        document.getElementById('institutionalHoldersNoData').style.display = 'none';

        const tableBody = document.getElementById('institutionalHoldersTable');
        tableBody.innerHTML = '';

        // Find the maximum percentage for scaling the bars
        const maxPercentage = Math.max(...holders.map(h => h.percent_held || 0));

        holders.forEach((holder, index) => {
            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid #f1f5f9';
            row.style.transition = 'background-color 0.2s';
            
            row.onmouseover = function() {
                this.style.backgroundColor = '#f8fafc';
            };
            row.onmouseout = function() {
                this.style.backgroundColor = '';
            };

            // Calculate percentage and bar width
            const percentage = holder.percent_held || 0;
            const percentageDisplay = holder.percent_held_display || 'N/A';
            const barWidth = maxPercentage > 0 ? (percentage / maxPercentage) * 100 : 0;

            row.innerHTML = `
                <td style="padding: 12px; color: #64748b; font-weight: 500;">${index + 1}</td>
                <td style="padding: 12px; color: #1e293b; font-weight: 500;">${holder.holder_name}</td>
                <td style="padding: 12px; text-align: right; color: #1e293b;">${holder.shares_display}</td>
                <td style="padding: 12px; text-align: right; color: #059669; font-weight: 600;">${holder.value_display}</td>
                <td class="percentage-cell">
                    ${this.createPercentageBar(percentageDisplay, barWidth)}
                </td>
                <td style="padding: 12px; text-align: right; color: #64748b; font-size: 13px;">${this.formatDate(holder.date_reported)}</td>
            `;

            tableBody.appendChild(row);
        });
    }

    /**
     * Create horizontal percentage bar element
     */
    createPercentageBar(percentageText, barWidth) {
        if (percentageText === 'N/A') {
            return `<span style="color: #64748b; font-size: 12px;">N/A</span>`;
        }

        // Position text to the right of the bar with some padding
        const textLeft = Math.min(barWidth + 8, 85); // 8px padding from bar, max 85% to avoid overflow
        
        return `
            <div class="percentage-bar-container">
                <div class="percentage-bar-fill" style="width: ${barWidth}%;"></div>
                <div class="percentage-bar-text" style="left: ${textLeft}%;">${percentageText}</div>
            </div>
        `;
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    /**
     * Show message when no data is available
     */
    showNoDataMessage() {
        document.getElementById('institutionalHoldersLoading').style.display = 'none';
        document.getElementById('institutionalHoldersContent').style.display = 'none';
        document.getElementById('institutionalHoldersNoData').style.display = 'block';
    }

    /**
     * Show error message
     */
    showErrorMessage(message) {
        document.getElementById('institutionalHoldersLoading').innerHTML = `
            <i class="fas fa-exclamation-triangle" style="color: #dc2626;"></i>
            <p style="color: #dc2626; margin-top: 10px;">${message}</p>
        `;
    }
}

// Initialize global instance
window.institutionalHoldersManager = new InstitutionalHoldersManager();

// Hook into symbol change and tab switching
document.addEventListener('DOMContentLoaded', function() {
    // Listen for symbol selection changes
    const symbolSelect = document.getElementById('symbolSelect');
    if (symbolSelect) {
        symbolSelect.addEventListener('change', function() {
            const symbol = this.value;
            if (symbol && window.institutionalHoldersManager) {
                // Load institutional holders when company-info tab is active
                const companyInfoTab = document.querySelector('[data-tab="company-info"]');
                if (companyInfoTab && companyInfoTab.classList.contains('active')) {
                    window.institutionalHoldersManager.loadInstitutionalHolders(symbol);
                }
            }
        });
    }

    // Listen for tab clicks
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Load institutional holders when company info tab is clicked
            if (tabName === 'company-info') {
                const symbolSelect = document.getElementById('symbolSelect');
                const symbol = symbolSelect ? symbolSelect.value : null;
                
                if (symbol && window.institutionalHoldersManager) {
                    window.institutionalHoldersManager.loadInstitutionalHolders(symbol);
                }
            }
        });
    });
});

