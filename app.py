"""
FraudShield AI - Top-level Application Entrypoint
================================================
Imports and exposes the FastAPI application instance from backend.app.
Enables running the application from project root via:
    uvicorn app:app --host 0.0.0.0 --port 7860
Or directly with:
    python app.py
"""

import os
import sys
from pathlib import Path

# Add project root and backend directory to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

for directory in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

from backend.app import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    print(f"[FraudShield AI] Launching on http://0.0.0.0:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
