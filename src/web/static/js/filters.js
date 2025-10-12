/**
 * Market Analysis Filters Manager
 * Handles sector, industry, and symbol filtering
 */

class FiltersManager {
    constructor() {
        this.sectorFilter = null;
        this.industryFilter = null;
        this.symbolSelect = null;
        this.allSymbols = [];
        
        this.init();
    }

    /**
     * Initialize the filters manager
     */
    async init() {
        // Get DOM elements
        this.sectorFilter = document.getElementById('sectorFilter');
        this.industryFilter = document.getElementById('industryFilter');
        this.symbolSelect = document.getElementById('symbolSelect');

        if (!this.sectorFilter || !this.industryFilter) {
            console.error('Filter elements not found');
            return;
        }

        // Setup event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadSectors();
        // Don't load symbols here - let charts.js handle it
    }

    /**
     * Setup event listeners for filter changes
     */
    setupEventListeners() {
        // Sector filter change
        this.sectorFilter.addEventListener('change', async () => {
            await this.onSectorChange();
        });

        // Industry filter change
        this.industryFilter.addEventListener('change', async () => {
            await this.onIndustryChange();
        });
    }

    /**
     * Load sectors from API
     */
    async loadSectors() {
        try {
            const response = await fetch('/api/company-info/filters/sectors');
            if (!response.ok) {
                throw new Error('Failed to load sectors');
            }

            const sectors = await response.json();
            
            // Clear existing options except the first one
            this.sectorFilter.innerHTML = '<option value="">All Sectors</option>';
            
            // Add sector options
            sectors.forEach(sector => {
                const option = document.createElement('option');
                option.value = sector;
                option.textContent = sector;
                this.sectorFilter.appendChild(option);
            });

            console.log(`Loaded ${sectors.length} sectors`);
        } catch (error) {
            console.error('Error loading sectors:', error);
        }
    }

    /**
     * Load industries from API (optionally filtered by sector)
     */
    async loadIndustries(sector = null) {
        try {
            let url = '/api/company-info/filters/industries';
            if (sector) {
                url += `?sector=${encodeURIComponent(sector)}`;
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to load industries');
            }

            const industries = await response.json();
            
            // Store current selection
            const currentIndustry = this.industryFilter.value;
            
            // Clear existing options except the first one
            this.industryFilter.innerHTML = '<option value="">All Industries</option>';
            
            // Add industry options
            industries.forEach(industry => {
                const option = document.createElement('option');
                option.value = industry;
                option.textContent = industry;
                this.industryFilter.appendChild(option);
            });

            // Restore selection if it still exists
            if (currentIndustry && industries.includes(currentIndustry)) {
                this.industryFilter.value = currentIndustry;
            }

            console.log(`Loaded ${industries.length} industries`);
        } catch (error) {
            console.error('Error loading industries:', error);
        }
    }

    /**
     * Load symbols (filtered or all)
     */
    async loadSymbols() {
        try {
            const sector = this.sectorFilter.value;
            const industry = this.industryFilter.value;

            let url = '/api/market-data/symbols';
            
            // If filters are applied, use company info endpoint
            if (sector || industry) {
                url = '/api/company-info/filters/symbols';
                const params = new URLSearchParams();
                if (sector) params.append('sector', sector);
                if (industry) params.append('industry', industry);
                url += `?${params.toString()}`;
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to load symbols');
            }

            let symbols;
            if (sector || industry) {
                // Company info endpoint returns array of strings
                symbols = await response.json();
                symbols = symbols.map(symbol => ({ symbol, record_count: 0 }));
            } else {
                // Market data endpoint returns array of objects
                symbols = await response.json();
            }

            this.allSymbols = symbols;
            
            // Store current selection
            const currentSymbol = this.symbolSelect.value;
            
            // Clear existing options except the first one
            this.symbolSelect.innerHTML = '<option value="">Select a symbol...</option>';
            
            // Add symbol options
            symbols.forEach(item => {
                const option = document.createElement('option');
                const symbol = typeof item === 'string' ? item : item.symbol;
                const count = typeof item === 'object' && item.record_count ? ` (${item.record_count} records)` : '';
                const name = typeof item === 'object' && item.name ? ` - ${item.name}` : '';
                
                option.value = symbol;
                option.textContent = `${symbol}${name}${count}`;
                this.symbolSelect.appendChild(option);
            });

            // Restore selection if it still exists
            if (currentSymbol && symbols.some(s => (typeof s === 'string' ? s : s.symbol) === currentSymbol)) {
                this.symbolSelect.value = currentSymbol;
            } else if (symbols.length > 0) {
                // Auto-select first symbol if current selection is not in filtered list
                const firstSymbol = typeof symbols[0] === 'string' ? symbols[0] : symbols[0].symbol;
                this.symbolSelect.value = firstSymbol;
                
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                this.symbolSelect.dispatchEvent(event);
            }

            console.log(`Loaded ${symbols.length} symbols`);
        } catch (error) {
            console.error('Error loading symbols:', error);
        }
    }

    /**
     * Handle sector filter change
     */
    async onSectorChange() {
        const sector = this.sectorFilter.value;
        console.log('Sector changed to:', sector || 'All');
        
        // Reload industries based on selected sector
        await this.loadIndustries(sector || null);
        
        // Reload symbols based on filters
        await this.loadSymbols();
    }

    /**
     * Handle industry filter change
     */
    async onIndustryChange() {
        const industry = this.industryFilter.value;
        console.log('Industry changed to:', industry || 'All');
        
        // Reload symbols based on filters
        await this.loadSymbols();
    }

    /**
     * Get currently selected filters
     */
    getFilters() {
        return {
            sector: this.sectorFilter?.value || null,
            industry: this.industryFilter?.value || null,
            symbol: this.symbolSelect?.value || null
        };
    }
}

// Initialize filters manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.filtersManager = new FiltersManager();
});

