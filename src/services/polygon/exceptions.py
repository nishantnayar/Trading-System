"""
Polygon.io API Exceptions
"""

from typing import Optional


class PolygonAPIError(Exception):
    """Base exception for Polygon API errors"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class PolygonAuthenticationError(PolygonAPIError):
    """Authentication error with Polygon API"""

    def __init__(self, message: str = "Invalid Polygon API credentials"):
        super().__init__(message, 401)


class PolygonRateLimitError(PolygonAPIError):
    """Rate limit exceeded for Polygon API"""

    def __init__(self, message: str = "Polygon API rate limit exceeded"):
        super().__init__(message, 429)


class PolygonConnectionError(PolygonAPIError):
    """Connection error with Polygon API"""

    def __init__(self, message: str = "Failed to connect to Polygon API"):
        super().__init__(message, 503)


class PolygonDataError(PolygonAPIError):
    """Data validation error for Polygon responses"""

    def __init__(self, message: str = "Invalid data received from Polygon API"):
        super().__init__(message)
