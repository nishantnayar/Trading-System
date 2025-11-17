"""
LLM Service for Stock Screener
Handles natural language queries and AI-powered analysis using Ollama
"""

import os
from typing import Any, Dict, List, Optional

import ollama
from loguru import logger


class LLMService:
    """Service for interacting with local LLM via Ollama"""
    
    def __init__(self, model: str = "phi3", base_url: Optional[str] = None):
        """
        Initialize LLM service
        
        Args:
            model: Model name to use (default: phi3)
            base_url: Custom Ollama base URL (default: http://localhost:11434)
        """
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Test connection
        try:
            self._test_connection()
        except Exception as e:
            logger.warning(f"LLM service initialization warning: {e}")
    
    def _test_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            # Try to list models to verify connection
            models = ollama.list()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise
    
    def interpret_screening_query(self, query: str) -> Dict[str, Any]:
        """
        Interpret natural language screening query into structured criteria
        
        Args:
            query: Natural language query (e.g., "Find tech stocks with RSI < 30")
            
        Returns:
            Dictionary with parsed screening criteria
        """
        prompt = f"""You are a financial analysis assistant. Parse this stock screening query into structured criteria.

Query: "{query}"

Extract the following information and return ONLY a JSON object with these fields:
- sector: string or null (e.g., "Technology", "Financial Services", "Healthcare", "Energy")
- industry: string or null
- min_price: float or null
- max_price: float or null
- min_volume: int or null
- min_market_cap: float or null (in billions)
- rsi_min: float or null (0-100) - ONLY if query specifies minimum RSI value
- rsi_max: float or null (0-100) - ONLY if query specifies maximum RSI value
- min_price_change_pct: float or null (percentage)
- max_price_change_pct: float or null (percentage)
- keywords: list of strings or null (ONLY for company name/symbol search, NOT for sectors or sorting terms like "highest", "lowest", "top")

IMPORTANT RULES:
1. If query mentions a sector (finance, tech, healthcare, etc.), put it in "sector" field, NOT keywords
2. Do NOT put sorting terms (highest, lowest, top, best) in keywords
3. Do NOT put indicator names (RSI, MACD) in keywords unless searching for company names
4. Common sectors: "Financial Services" (for finance/financial), "Technology" (for tech), "Healthcare" (for health/medical)

Return ONLY valid JSON, no explanations. If a field cannot be determined, use null.

Example responses:
Query: "find finance stock with highest rsi"
Response: {{"sector": "Financial Services", "rsi_min": null, "rsi_max": null, "keywords": null}}

Query: "Find tech stocks with RSI < 30"
Response: {{"sector": "Technology", "rsi_max": 30, "keywords": null}}

Query: "Show me Apple stock"
Response: {{"sector": null, "keywords": ["Apple"]}}
"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.1,  # Low temperature for structured output
                }
            )
            
            content = response['message']['content'].strip()
            
            # Extract JSON from response (might have markdown code blocks)
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            import json
            criteria = json.loads(content)
            
            logger.info(f"Parsed query '{query}' into criteria: {criteria}")
            return criteria
            
        except Exception as e:
            logger.error(f"Error interpreting query: {e}")
            # Return empty criteria on error
            return {}
    
    def analyze_screened_results(
        self, 
        results: List[Dict[str, Any]], 
        query: Optional[str] = None
    ) -> str:
        """
        Generate AI analysis of screened stock results
        
        Args:
            results: List of screened stock results
            query: Original query (optional)
            
        Returns:
            Analysis text
        """
        if not results:
            return "No stocks matched the screening criteria."
        
        # Prepare summary data
        num_results = len(results)
        sectors = {}
        avg_rsi = 0
        rsi_count = 0
        
        for stock in results:
            # Count sectors
            sector = stock.get('sector', 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + 1
            
            # Calculate average RSI
            if stock.get('rsi') is not None:
                avg_rsi += stock['rsi']
                rsi_count += 1
        
        avg_rsi = avg_rsi / rsi_count if rsi_count > 0 else None
        
        # Build prompt
        summary = f"Found {num_results} stocks"
        if avg_rsi:
            summary += f" with average RSI of {avg_rsi:.1f}"
        if sectors:
            top_sector = max(sectors.items(), key=lambda x: x[1])
            summary += f". Top sector: {top_sector[0]} ({top_sector[1]} stocks)"
        
        prompt = f"""You are a financial analyst. Analyze these stock screening results and provide insights.

Query: {query or 'General screening'}
Results Summary: {summary}
Number of results: {num_results}

Provide a brief analysis (2-3 sentences) highlighting:
1. Key patterns or trends in the results
2. Notable opportunities or risks
3. Any interesting observations

Be concise and professional.
"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.7,
                }
            )
            
            analysis = response['message']['content'].strip()
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return f"Analysis generated for {num_results} stocks. Review the results above for details."
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        try:
            models = ollama.list()
            model_list = []
            
            if hasattr(models, 'models'):
                for model in models.models:
                    if hasattr(model, 'model'):
                        model_list.append({
                            'name': model.model.split(':')[0],
                            'full_name': model.model,
                            'size': getattr(model, 'size', 0),
                            'details': getattr(model, 'details', None)
                        })
            
            return {
                'available_models': model_list,
                'current_model': self.model
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {'available_models': [], 'current_model': self.model}


def get_llm_service(model: str = "phi3") -> LLMService:
    """Get or create LLM service instance"""
    return LLMService(model=model)

