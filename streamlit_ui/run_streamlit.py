"""
Run script for Streamlit Trading System UI
"""

import subprocess
import sys

def run_streamlit():
    """Run Streamlit with correct settings"""
    try:
        # Run streamlit with localhost binding
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_ui/streamlit_app.py",
            "--server.address", "localhost",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\nStreamlit app stopped.")
    except Exception as e:
        print(f"Error running Streamlit: {e}")

if __name__ == "__main__":
    run_streamlit()
