/**
 * Technical Indicators Library for Trading Charts
 * Provides professional-grade calculations for MACD, RSI, SMA, EMA
 */

class TechnicalIndicators {
    /**
     * Calculate Simple Moving Average (SMA)
     * @param {Array} data - Array of values
     * @param {number} period - Period for SMA
     * @returns {Array} Array of SMA values
     */
    static SMA(data, period) {
        const result = [];
        
        for (let i = 0; i < data.length; i++) {
            if (i < period - 1) {
                result.push(null);
                continue;
            }
            
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i - j];
            }
            result.push(sum / period);
        }
        
        return result;
    }

    /**
     * Calculate Exponential Moving Average (EMA)
     * @param {Array} data - Array of values
     * @param {number} period - Period for EMA
     * @returns {Array} Array of EMA values
     */
    static EMA(data, period) {
        const result = [];
        const multiplier = 2 / (period + 1);
        
        // First EMA is SMA
        let sum = 0;
        for (let i = 0; i < period; i++) {
            sum += data[i];
            result.push(null);
        }
        
        let ema = sum / period;
        result[period - 1] = ema;
        
        // Calculate remaining EMAs
        for (let i = period; i < data.length; i++) {
            ema = (data[i] - ema) * multiplier + ema;
            result.push(ema);
        }
        
        return result;
    }

    /**
     * Calculate MACD (Moving Average Convergence Divergence)
     * @param {Array} data - Array of close prices
     * @param {number} fastPeriod - Fast EMA period (default 12)
     * @param {number} slowPeriod - Slow EMA period (default 26)
     * @param {number} signalPeriod - Signal line period (default 9)
     * @returns {Object} Object containing macd, signal, and histogram arrays
     */
    static MACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        const fastEMA = this.EMA(data, fastPeriod);
        const slowEMA = this.EMA(data, slowPeriod);
        
        // MACD Line = Fast EMA - Slow EMA
        const macdLine = fastEMA.map((fast, i) => {
            if (fast === null || slowEMA[i] === null) return null;
            return fast - slowEMA[i];
        });
        
        // Signal Line = EMA of MACD Line
        const validMacd = macdLine.filter(v => v !== null);
        const signalEMA = this.EMA(validMacd, signalPeriod);
        
        // Fill signal line with nulls at the start
        const nullCount = macdLine.findIndex(v => v !== null) + signalPeriod - 1;
        const signalLine = new Array(nullCount).fill(null).concat(signalEMA.filter(v => v !== null));
        
        // Histogram = MACD Line - Signal Line
        const histogram = macdLine.map((macd, i) => {
            if (macd === null || signalLine[i] === null) return null;
            return macd - signalLine[i];
        });
        
        return {
            macd: macdLine,
            signal: signalLine,
            histogram: histogram
        };
    }

    /**
     * Calculate RSI (Relative Strength Index)
     * @param {Array} data - Array of close prices
     * @param {number} period - Period for RSI (default 14)
     * @returns {Array} Array of RSI values
     */
    static RSI(data, period = 14) {
        const result = [];
        const gains = [];
        const losses = [];
        
        // Calculate price changes
        for (let i = 1; i < data.length; i++) {
            const change = data[i] - data[i - 1];
            gains.push(change > 0 ? change : 0);
            losses.push(change < 0 ? Math.abs(change) : 0);
        }
        
        // First RSI uses SMA
        result.push(null); // No RSI for first data point
        
        for (let i = 0; i < period - 1; i++) {
            result.push(null);
        }
        
        // Calculate first average gain and loss
        let avgGain = 0;
        let avgLoss = 0;
        for (let i = 0; i < period; i++) {
            avgGain += gains[i];
            avgLoss += losses[i];
        }
        avgGain /= period;
        avgLoss /= period;
        
        // Calculate first RSI
        const rs = avgGain / (avgLoss === 0 ? 1 : avgLoss);
        const rsi = 100 - (100 / (1 + rs));
        result.push(rsi);
        
        // Calculate subsequent RSIs using smoothed averages
        for (let i = period; i < gains.length; i++) {
            avgGain = ((avgGain * (period - 1)) + gains[i]) / period;
            avgLoss = ((avgLoss * (period - 1)) + losses[i]) / period;
            
            const rs = avgGain / (avgLoss === 0 ? 1 : avgLoss);
            const rsi = 100 - (100 / (1 + rs));
            result.push(rsi);
        }
        
        return result;
    }

    /**
     * Calculate Bollinger Bands
     * @param {Array} data - Array of close prices
     * @param {number} period - Period for moving average (default 20)
     * @param {number} stdDev - Standard deviation multiplier (default 2)
     * @returns {Object} Object containing upper, middle, and lower bands
     */
    static BollingerBands(data, period = 20, stdDev = 2) {
        const sma = this.SMA(data, period);
        const upper = [];
        const lower = [];
        
        for (let i = 0; i < data.length; i++) {
            if (sma[i] === null) {
                upper.push(null);
                lower.push(null);
                continue;
            }
            
            // Calculate standard deviation
            let sumSquares = 0;
            for (let j = 0; j < period; j++) {
                const diff = data[i - j] - sma[i];
                sumSquares += diff * diff;
            }
            const std = Math.sqrt(sumSquares / period);
            
            upper.push(sma[i] + (stdDev * std));
            lower.push(sma[i] - (stdDev * std));
        }
        
        return {
            upper: upper,
            middle: sma,
            lower: lower
        };
    }

    /**
     * Format volume for display (K, M, B)
     * @param {number} volume - Volume value
     * @returns {string} Formatted volume string
     */
    static formatVolume(volume) {
        if (volume >= 1e9) return (volume / 1e9).toFixed(2) + 'B';
        if (volume >= 1e6) return (volume / 1e6).toFixed(2) + 'M';
        if (volume >= 1e3) return (volume / 1e3).toFixed(2) + 'K';
        return volume.toString();
    }

    /**
     * Format price with appropriate decimal places
     * @param {number} price - Price value
     * @returns {string} Formatted price string
     */
    static formatPrice(price) {
        if (price === null || price === undefined) return '-';
        if (price < 1) return price.toFixed(4);
        if (price < 100) return price.toFixed(2);
        return price.toFixed(2);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TechnicalIndicators;
}

