API Reference
=============

This section provides comprehensive API documentation for the Trading System.

.. toctree::
   :maxdepth: 2

   data-ingestion
   strategy-engine
   execution
   risk-management
   analytics
   system-health

Overview
--------

The Trading System provides a comprehensive REST API for all trading operations. The API is built with FastAPI and provides:

* **RESTful Endpoints**: Standard HTTP methods and status codes
* **OpenAPI Documentation**: Interactive API documentation
* **Type Safety**: Pydantic models for request/response validation
* **Authentication**: Secure API access
* **Rate Limiting**: Protection against abuse
* **Monitoring**: Comprehensive logging and metrics

API Base URL
------------

* **Development**: http://localhost:8000/api/v1
* **Production**: https://your-domain.com/api/v1

Authentication
---------------

The API uses API key authentication:

.. code-block:: http

   GET /api/v1/health
   X-API-Key: your-api-key-here

Response Format
----------------

All API responses follow a consistent format:

.. code-block:: json

   {
     "success": true,
     "data": { ... },
     "message": "Operation completed successfully",
     "timestamp": "2025-09-27T21:36:00Z"
   }

Error Handling
---------------

The API provides detailed error responses:

.. code-block:: json

   {
     "success": false,
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "Invalid input parameters",
       "details": { ... }
     },
     "timestamp": "2025-09-27T21:36:00Z"
   }

Rate Limiting
--------------

* **Standard**: 1000 requests per hour
* **Premium**: 5000 requests per hour
* **Enterprise**: Custom limits

Monitoring
----------

* **Health Checks**: System status endpoints
* **Metrics**: Performance and usage statistics
* **Logs**: Structured logging for debugging
* **Alerts**: Automated monitoring and notifications
