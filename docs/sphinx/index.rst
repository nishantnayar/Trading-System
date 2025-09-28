Trading System Documentation
===========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user-guide/index
   api/index
   development/index

Welcome to the Trading System's technical documentation!

This documentation provides comprehensive information about the trading system's architecture, API, and development guidelines.

Overview
--------

The Trading System is a production-grade algorithmic trading platform designed for equities trading through Alpaca. It features:

* **Microservices Architecture**: Scalable and maintainable service design
* **Real-time Data Processing**: Live market data ingestion and analysis
* **Strategy Engine**: Plugin-based framework for custom trading strategies
* **Risk Management**: Built-in position sizing and risk controls
* **Analytics**: Comprehensive performance tracking and reporting
* **Modern Tech Stack**: Python, FastAPI, PostgreSQL, Redis, Polars

Quick Start
-----------

1. **Clone the repository**:
   .. code-block:: bash

      git clone https://github.com/nishantnayar/trading-system.git
      cd trading-system

2. **Activate your conda environment**:
   .. code-block:: bash

      conda activate your-environment-name

3. **Install dependencies**:
   .. code-block:: bash

      pip install -r deployment/requirements.txt

4. **Configure environment**:
   .. code-block:: bash

      cp deployment/env.example .env

5. **Start the system**:
   .. code-block:: bash

      python deployment/scripts/start_services.py

Architecture
------------

The system uses a microservices architecture with the following components:

* **Data Ingestion Service**: Market data processing and storage
* **Strategy Engine**: Algorithm execution and management
* **Execution Service**: Order management and trade execution
* **Risk Management**: Position sizing and risk controls
* **Analytics Service**: Performance tracking and reporting
* **Notification Service**: Alerts and notifications

Technology Stack
----------------

* **Backend**: Python 3.9+, FastAPI, Pydantic
* **Database**: PostgreSQL, Redis
* **Data Processing**: Polars
* **Orchestration**: Prefect
* **Frontend**: HTMX, Plotly, Tailwind CSS
* **Logging**: Loguru
* **Documentation**: MkDocs, Sphinx

API Reference
--------------

The system provides comprehensive APIs for:

* **Data Ingestion**: Market data processing endpoints
* **Strategy Management**: Algorithm configuration and execution
* **Risk Controls**: Position sizing and exposure management
* **Analytics**: Performance metrics and reporting
* **System Health**: Monitoring and diagnostics

Development
-----------

For developers working on the system:

* **Architecture Overview**: System design and components
* **Logging Architecture**: Comprehensive logging strategy
* **Contributing Guidelines**: Development standards and practices
* **Testing**: Quality assurance and validation
* **Deployment**: Production deployment procedures

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
