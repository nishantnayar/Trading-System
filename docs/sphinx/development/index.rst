Development Guide
=================

This section provides comprehensive development documentation for the Trading System.

.. toctree::
   :maxdepth: 2

   architecture
   logging-architecture
   contributing
   testing
   deployment
   troubleshooting

Overview
--------

The Trading System is built with modern Python technologies and follows best practices for:

* **Code Quality**: Flake8, Black, isort, mypy
* **Testing**: pytest with comprehensive coverage
* **Documentation**: MkDocs and Sphinx
* **CI/CD**: Automated quality checks and deployment
* **Monitoring**: Structured logging and metrics

Architecture
------------

The system uses a microservices architecture with:

* **Service Separation**: Independent, loosely coupled services
* **API Gateway**: Centralized request routing
* **Database**: PostgreSQL for persistent data
* **Cache**: Redis for high-speed access
* **Orchestration**: Prefect for workflow management
* **Monitoring**: Comprehensive logging and metrics

Technology Stack
----------------

* **Backend**: Python 3.9+, FastAPI, Pydantic
* **Database**: PostgreSQL, Redis
* **Data Processing**: Polars
* **Orchestration**: Prefect
* **Frontend**: HTMX, Plotly, Tailwind CSS
* **Logging**: Loguru
* **Testing**: pytest, coverage
* **Documentation**: MkDocs, Sphinx

Development Setup
-----------------

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

4. **Install development dependencies**:
   .. code-block:: bash

      pip install -r deployment/requirements-dev.txt

5. **Run tests**:
   .. code-block:: bash

      pytest

Code Standards
---------------

* **PEP 8**: Python style guide compliance
* **Type Hints**: Comprehensive type annotations
* **Docstrings**: Google-style documentation
* **Testing**: Minimum 80% code coverage
* **Linting**: Automated quality checks

Contributing
------------

We welcome contributions! Please see our :doc:`contributing` guide for:

* **Code Standards**: Development guidelines
* **Pull Requests**: Submission process
* **Testing**: Quality assurance
* **Documentation**: Keeping docs up to date
