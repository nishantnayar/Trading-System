"""
Main entry point for the Trading System API.

The FastAPI app (routers, middleware, lifespan) lives in src/web/main.py.
This wrapper only enforces the conda env and runs uvicorn - register new
routers in src/web/main.py, not here.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def _check_conda_env(expected: str = "torch_gpu") -> None:
    """Fail fast if this process is not running in the expected conda env."""
    actual = os.environ.get("CONDA_DEFAULT_ENV")
    if actual != expected:
        sys.exit(
            f"Wrong Python environment: expected conda env '{expected}', "
            f"got '{actual or 'none (not a conda env)'}'. "
            f"Activate it with: conda activate {expected}"
        )


_check_conda_env()

from src.web.main import app  # noqa: E402,F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
