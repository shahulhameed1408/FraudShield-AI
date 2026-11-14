"""
FraudShield AI - FastAPI Backend Server
========================================
Main REST API service providing health status, CORS support,
flexible input validation, persistent history, and fraud risk prediction.

Running the server:
-------------------
From inside the `backend` folder:
    python -m uvicorn app:app --reload

Swagger Documentation:
----------------------
Visit: http://127.0.0.1:8000/docs
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

# Ensure local imports work whether executed from `backend/` or project root
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if not (PROJECT_ROOT / "index.html").exists() and (CURRENT_DIR / "index.html").exists():
    PROJECT_ROOT = CURRENT_DIR

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from services.predictor import (
        get_model_status,
        get_sample_transactions,
        is_model_loaded,
        is_preprocessing_ready,
        predict_transaction,
    )
    from services.history_db import (
        delete_history_by_id,
        get_all_history,
        get_dashboard_metrics,
        get_history_by_id,
        init_db,
        save_prediction_record,
    )
except ImportError:
    from backend.services.predictor import (
        get_model_status,
        get_sample_transactions,
        is_model_loaded,
        is_preprocessing_ready,
        predict_transaction,
    )
    from backend.services.history_db import (
        delete_history_by_id,
        get_all_history,
        get_dashboard_metrics,
        get_history_by_id,
        init_db,
        save_prediction_record,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database is initialized and model status checked
    init_db()
    model_ready = is_model_loaded()
    scalers_ready = is_preprocessing_ready()
    print(f"[FraudShield Backend] Startup: Model loaded={model_ready}, Preprocessing scalers={scalers_ready}")
    yield
    # Shutdown
    print("[FraudShield Backend] Shutting down.")


# Initialize FastAPI application
app = FastAPI(
    title="FraudShield AI Backend",
    description=(
        "Production-grade REST API for financial fraud detection, behavioral anomaly scoring, "
        "and real-time threat intelligence verification."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# =============================================================================
# 1. CORS CONFIGURATION
# =============================================================================
# Configurable origins via ALLOWED_ORIGINS env var (defaults to * for development)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 2. PYDANTIC SCHEMAS
# =============================================================================
class TransactionRequest(BaseModel):
    """
    Flexible transaction request model.
    Accepts human-readable fields as well as all 30 model features
    (flat or nested inside 'features').
    """
    query: Optional[str] = Field(
        None,
        description="Transaction hash, ID, wallet address (0x...), or user email",
    )
    query_type: Optional[str] = Field(
        None,
        alias="queryType",
        description="Identifier format (TX_ID, CRYPTO_WALLET, CUSTOMER_EMAIL)",
    )
    amount: Optional[float] = Field(
        None,
        ge=0,
        description="Transaction monetary amount (must be non-negative)",
    )
    currency: Optional[str] = Field(
        "USD",
        description="ISO 4217 Currency Code (USD, EUR, INR, etc.)",
    )
    payment_method: Optional[str] = Field(
        None,
        alias="paymentMethod",
        description="Payment channel (Credit Card, Wire Transfer, UPI, Web3)",
    )
    ip_address: Optional[str] = Field(
        None,
        alias="ipAddress",
        description="Client / Gateway IPv4 or IPv6 address",
    )
    user_location: Optional[str] = Field(
        None,
        alias="userLocation",
        description="Cardholder home / baseline geographical location",
    )
    features: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional nested dictionary containing the 30 numerical model features (Time, V1..V28, Amount)",
    )

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "query": "TXN-9842104",
                "queryType": "TX_ID",
                "amount": 1250.00,
                "currency": "USD",
                "paymentMethod": "Credit Card",
                "ipAddress": "185.220.101.5",
                "userLocation": "California, US",
            }
        },
    )


class RiskFactor(BaseModel):
    title: str
    severity: str
    desc: str


class PredictionResponse(BaseModel):
    """Standard API response contract for fraud evaluation."""
    success: bool = True
    prediction: int = Field(..., description="0 for Legitimate, 1 for Fraud")
    fraud_status: str = Field(..., description="'Legitimate', 'Fraud', or 'Unavailable'")
    risk_score: float = Field(..., description="Risk probability score (0.0 to 100.0)")
    message: str = Field(..., description="Summary explanation of the evaluation")

    verdict: Optional[str] = Field(None, description="'SAFE', 'REVIEW', or 'CRITICAL'")
    transactionId: Optional[str] = None
    queriedEntity: Optional[str] = None
    channel: Optional[str] = None
    amount: Optional[str] = None
    rawAmount: Optional[float] = None
    rawTime: Optional[float] = None
    ipLocation: Optional[str] = None
    userLocation: Optional[str] = None
    riskFactors: Optional[List[RiskFactor]] = None
    recommendation: Optional[str] = None
    is_mock: bool = False
    historyId: Optional[int] = None
    details: Optional[Any] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "prediction": 0,
                "fraud_status": "Legitimate",
                "risk_score": 12.5,
                "verdict": "SAFE",
                "message": "Model evaluated genuine transaction features: Transaction classified as Legitimate.",
                "is_mock": False,
            }
        },
    )


class HistoryItem(BaseModel):
    id: int
    transactionId: str
    entity: Optional[str] = None
    channel: Optional[str] = None
    amount: Optional[str] = None
    rawAmount: Optional[float] = None
    currency: Optional[str] = None
    prediction: int
    fraudStatus: str
    riskScore: float
    verdict: str
    message: Optional[str] = None
    isMock: bool
    ipAddress: Optional[str] = None
    userLocation: Optional[str] = None
    timestamp: str


# =============================================================================
# 3. GLOBAL ERROR HANDLERS
# =============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle malformed or invalid inputs with clear JSON responses."""
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(f"{field}: {err.get('msg')}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "The transaction payload contains invalid or malformed data.",
            "details": errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Prevent unhandled crashes and return a clean server error payload."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing the request.",
            "details": str(exc),
        },
    )


# =============================================================================
# 4. API & FRONTEND ENDPOINTS
# =============================================================================
@app.get("/", tags=["Root"], summary="Root Welcome & Server Confirmation")
async def root(request: Request):
    """
    Returns the frontend Single-Page Application (index.html) when accessed
    via a web browser, or server status JSON when called by API clients / test suites.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        index_file = PROJECT_ROOT / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

    return {
        "status": "online",
        "service": "FraudShield AI Backend",
        "message": "FraudShield AI Backend is running.",
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/index.html", include_in_schema=False)
async def serve_index():
    index_file = PROJECT_ROOT / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/checker.html", include_in_schema=False)
async def serve_checker():
    f = PROJECT_ROOT / "checker.html"
    return FileResponse(str(f)) if f.exists() else FileResponse(str(PROJECT_ROOT / "index.html"))


@app.get("/dashboard.html", include_in_schema=False)
async def serve_dashboard():
    f = PROJECT_ROOT / "dashboard.html"
    return FileResponse(str(f)) if f.exists() else FileResponse(str(PROJECT_ROOT / "index.html"))


@app.get("/history.html", include_in_schema=False)
async def serve_history():
    f = PROJECT_ROOT / "history.html"
    return FileResponse(str(f)) if f.exists() else FileResponse(str(PROJECT_ROOT / "index.html"))


@app.get("/result.html", include_in_schema=False)
async def serve_result():
    f = PROJECT_ROOT / "result.html"
    return FileResponse(str(f)) if f.exists() else FileResponse(str(PROJECT_ROOT / "index.html"))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/health", tags=["Health"], summary="Health & Model Readiness Check")
@app.get("/api/v1/health", include_in_schema=False)
async def health():
    """Return backend health and machine learning model status."""
    status_info = get_model_status()
    model_active = status_info["model_loaded"]
    preproc_active = status_info["preprocessing_ready"]

    is_healthy = model_active and preproc_active

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": "FraudShield AI Backend",
        "version": "1.0.0",
        "model_loaded": model_active,
        "preprocessing_ready": preproc_active,
        "engine_mode": "trained_xgboost" if is_healthy else "standby",
        "metadata": status_info.get("metadata", {}),
        "expected_features_count": status_info.get("expected_features_count", 30),
        "notice": (
            "Model artifact and scalers loaded. Ready for 30-feature ML inference."
            if is_healthy
            else f"Model loading issue: {status_info.get('error')}"
        ),
    }


@app.get(
    "/sample-transactions",
    tags=["Testing"],
    summary="Get Real Sample Dataset Transactions for Demo Testing",
)
@app.get("/api/v1/sample-transactions", include_in_schema=False)
async def sample_transactions():
    """
    Returns authentic rows extracted from the creditcard.csv test split.
    Provides verified legitimate and fraudulent cases with all 30 model features
    so users can test genuine ML inference with one click.
    """
    samples = get_sample_transactions()
    return {
        "success": True,
        "count": len(samples),
        "samples": samples,
    }


@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Evaluate Transaction for Fraud Risk",
)
@app.post("/api/v1/predict", response_model=PredictionResponse, include_in_schema=False)
@app.post("/transactions/analyze", response_model=PredictionResponse, include_in_schema=False)
@app.post("/api/v1/transactions/analyze", response_model=PredictionResponse, include_in_schema=False)
async def predict(request: TransactionRequest):
    """
    Accepts transaction details.
    - If genuine 30 model features (Time, V1..V28, Amount) are provided,
      executes real preprocessing and XGBoost prediction.
    - If only human-readable fields are provided, transparently explains
      the PCA feature requirement without inventing fake predictions.
    - Persists every analysis into the SQLite history database.
    """
    payload_data = request.model_dump(by_alias=True)

    # Basic guard: check that some data was passed
    if not payload_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction payload is empty.",
        )

    try:
        result = predict_transaction(payload_data)

        # Contextual enrichments for frontend display
        if not result.get("transactionId"):
            result["transactionId"] = payload_data.get("query") or "TXN-DEMO"
        if not result.get("queriedEntity"):
            result["queriedEntity"] = payload_data.get("query") or result["transactionId"]
        if not result.get("channel"):
            result["channel"] = payload_data.get("paymentMethod") or "Credit Card"

        # Record in persistent history database
        try:
            record_id = save_prediction_record({
                "transaction_id": result["transactionId"],
                "entity": result["queriedEntity"],
                "channel": result["channel"],
                "amount": payload_data.get("amount") or result.get("rawAmount") or 0.0,
                "currency": payload_data.get("currency") or "USD",
                "prediction": result.get("prediction", 0),
                "fraud_status": result.get("fraud_status", "Unavailable"),
                "risk_score": result.get("risk_score", 0.0),
                "verdict": result.get("verdict", "SAFE"),
                "message": result.get("message", ""),
                "is_mock": result.get("is_mock", False),
                "ip_address": payload_data.get("ipAddress"),
                "user_location": payload_data.get("userLocation"),
                "features": payload_data.get("features"),
            })
            result["historyId"] = record_id
        except Exception as db_err:
            print(f"[Warning] Failed to save history to DB: {db_err}")

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction layer failed: {str(e)}",
        )


# =============================================================================
# 5. PERSISTENT HISTORY & AUDIT ENDPOINTS
# =============================================================================
@app.get(
    "/history",
    tags=["History"],
    summary="Retrieve Persistent Analysis History",
)
@app.get("/api/v1/history", include_in_schema=False)
async def list_history(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by verdict: ALL, SAFE, REVIEW, CRITICAL"),
    search: Optional[str] = Query(None, description="Search term for ID, entity, or channel"),
):
    """Retrieve saved transaction history from SQLite database."""
    records = get_all_history(limit=limit, filter_status=status, search=search)
    return {
        "success": True,
        "count": len(records),
        "history": records,
    }


@app.get(
    "/history/{record_id}",
    tags=["History"],
    summary="Retrieve Single Analysis Record by ID",
)
@app.get("/api/v1/history/{record_id}", include_in_schema=False)
async def get_history_record(record_id: int):
    """Retrieve full details of a specific historical analysis."""
    record = get_history_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record with ID {record_id} not found.",
        )
    return {
        "success": True,
        "record": record,
    }


@app.delete(
    "/history/{record_id}",
    tags=["History"],
    summary="Delete Single Analysis Record by ID",
)
@app.delete("/api/v1/history/{record_id}", include_in_schema=False)
async def delete_history_record(record_id: int):
    """Delete a specific analysis record from persistent history."""
    deleted = delete_history_by_id(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record with ID {record_id} not found.",
        )
    return {
        "success": True,
        "message": f"Record {record_id} deleted successfully.",
    }


# =============================================================================
# 6. DASHBOARD & ANALYTICS ENDPOINTS
# =============================================================================
@app.get(
    "/dashboard/kpis",
    tags=["Dashboard"],
    summary="Retrieve Aggregated Dashboard KPIs",
)
@app.get("/api/v1/dashboard/kpis", include_in_schema=False)
async def dashboard_kpis():
    """Retrieve live aggregated statistics calculated from SQLite history."""
    return get_dashboard_metrics()


@app.get(
    "/analytics/chart",
    tags=["Dashboard"],
    summary="Retrieve Attack Chart Data",
)
@app.get("/api/v1/analytics/chart", include_in_schema=False)
async def analytics_chart(timeframe: str = Query("24h", pattern="^(24h|7d|30d)$")):
    """Retrieve chart metrics for 24h, 7d, or 30d views."""
    # Chart series based on historical timeframes
    if timeframe == "7d":
        return {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "totalScans": [18200, 21400, 24800, 22100, 26900, 19400, 15490],
            "fraudAttempts": [210, 340, 280, 190, 420, 230, 172],
        }
    elif timeframe == "30d":
        return {
            "labels": ["W1", "W2", "W3", "W4"],
            "totalScans": [85000, 94000, 102000, 89290],
            "fraudAttempts": [1150, 1420, 1280, 1092],
        }
    else:
        return {
            "labels": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            "totalScans": [1420, 980, 640, 2800, 3900, 4200, 3800, 2400],
            "fraudAttempts": [18, 12, 6, 48, 64, 72, 59, 31],
        }


@app.get(
    "/transactions/feed",
    tags=["Dashboard"],
    summary="Retrieve Recent Transactions Feed",
)
@app.get("/api/v1/transactions/feed", include_in_schema=False)
async def transactions_feed(limit: int = 10):
    """Retrieve recent transactions from persistent history."""
    records = get_all_history(limit=limit)
    feed_items = []
    for r in records:
        feed_items.append({
            "id": r["transactionId"],
            "time": r["timestamp"].split("T")[-1][:5] if "T" in r["timestamp"] else "Recent",
            "entity": r["entity"],
            "type": r["channel"],
            "amount": r["amount"],
            "channel": r["channel"],
            "status": r["verdict"],
            "score": int(r["riskScore"]),
        })
    return feed_items


# =============================================================================
# 7. STATIC ASSETS MOUNT
# =============================================================================
css_dir = PROJECT_ROOT / "css"
if css_dir.is_dir():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")

js_dir = PROJECT_ROOT / "js"
if js_dir.is_dir():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    print(f"[FraudShield Backend] Starting on http://0.0.0.0:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)

