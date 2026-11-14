"""
FraudShield AI - Machine Learning Prediction Service
===================================================
Production prediction service that loads the versioned XGBoost artifact,
applies the exact StandardScaler transformations to Time and Amount,
validates all 30 model features, and executes real inference.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
MODEL_DIR = CURRENT_DIR.parent / "model"
BUNDLE_PATH = MODEL_DIR / "fraud_detection_bundle.joblib"
MODEL_PATH = MODEL_DIR / "fraud_detection_model.pkl"
SAMPLE_TX_PATH = MODEL_DIR / "sample_transactions.json"

# Expected 30 features in exact training order
REQUIRED_FEATURES: List[str] = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]

_bundle: Optional[Dict[str, Any]] = None
_model: Any = None
_scaler_time: Any = None
_scaler_amount: Any = None
_model_error: Optional[str] = None
_model_metadata: Dict[str, Any] = {}


def load_model_artifact(force_reload: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Load the trained model and preprocessing scalers.
    Supports bundled joblib artifacts as well as fallback pickled artifacts.
    """
    global _bundle, _model, _scaler_time, _scaler_amount, _model_error, _model_metadata

    if _model is not None and not force_reload:
        return True, None

    # Check potential artifact paths (bundle first, then pkl)
    load_path = None
    if BUNDLE_PATH.exists():
        load_path = BUNDLE_PATH
    elif MODEL_PATH.exists():
        load_path = MODEL_PATH
    else:
        _model_error = f"Model artifact not found at {BUNDLE_PATH} or {MODEL_PATH}."
        return False, _model_error

    try:
        loaded = joblib.load(load_path)

        if isinstance(loaded, dict) and "model" in loaded:
            # Bundled dictionary artifact
            _bundle = loaded
            _model = loaded["model"]
            _scaler_time = loaded.get("scaler_time")
            _scaler_amount = loaded.get("scaler_amount")
            _model_metadata = {
                "version": loaded.get("model_version", "v1.0.0"),
                "trained_at": loaded.get("trained_at"),
                "metrics": loaded.get("metrics", {}),
                "description": loaded.get("description", "FraudShield XGBoost Classifier"),
            }
        else:
            # Raw model object without bundled scalers
            _model = loaded
            _scaler_time = None
            _scaler_amount = None
            _model_metadata = {
                "version": "legacy-unbundled",
                "metrics": {},
                "description": "Legacy model file (preprocessing scalers missing)",
            }

        _model_error = None
        return True, None

    except Exception as exc:
        _model = None
        _scaler_time = None
        _scaler_amount = None
        _model_error = f"Failed to load model artifact: {str(exc)}"
        return False, _model_error


# Attempt immediate load at startup
load_model_artifact()


def is_model_loaded() -> bool:
    """Return True if model is loaded and ready."""
    return _model is not None


def is_preprocessing_ready() -> bool:
    """Return True if both Time and Amount scalers are loaded."""
    return _scaler_time is not None and _scaler_amount is not None


def get_model_status() -> Dict[str, Any]:
    """Return comprehensive health and readiness diagnostic details."""
    ready = is_model_loaded()
    scalers_ready = is_preprocessing_ready()

    return {
        "model_loaded": ready,
        "preprocessing_ready": scalers_ready,
        "artifact_path": str(BUNDLE_PATH if BUNDLE_PATH.exists() else MODEL_PATH),
        "error": _model_error,
        "metadata": _model_metadata,
        "expected_features_count": len(REQUIRED_FEATURES),
        "expected_features": REQUIRED_FEATURES,
    }


def get_sample_transactions() -> List[Dict[str, Any]]:
    """Return real dataset rows extracted from the test split for genuine testing."""
    if SAMPLE_TX_PATH.exists():
        try:
            with open(SAMPLE_TX_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _extract_and_validate_features(
    data: Dict[str, Any]
) -> Tuple[Optional[pd.DataFrame], Optional[Dict[str, Any]]]:
    """
    Extracts the 30 numerical features from request data and validates them.
    Supports either flat dictionary or nested 'features' dictionary.
    Rejects missing, non-numeric, NaN, and Infinite values.
    """
    feature_source: Dict[str, Any] = {}

    # Check if features are wrapped under a 'features' dictionary
    if "features" in data and isinstance(data["features"], dict):
        feature_source = data["features"]
    else:
        # Check flat data
        feature_source = data

    # Check for presence of all 30 features
    missing_features = [f for f in REQUIRED_FEATURES if f not in feature_source]

    if missing_features:
        # Check if the user passed standard human-readable transaction fields instead
        human_keys = {"query", "paymentMethod", "payment_method", "currency", "ipAddress", "ip_address", "userLocation", "user_location"}
        has_human_fields = any(k in data for k in human_keys)

        if has_human_fields and len(missing_features) >= 28:
            return None, {
                "success": False,
                "prediction": 0,
                "fraud_status": "Unavailable",
                "risk_score": 0.0,
                "verdict": "REVIEW",
                "is_mock": True,
                "error_type": "PCA_FEATURE_MISMATCH",
                "message": (
                    "The trained XGBoost model requires 30 anonymized PCA features ('Time', 'V1'-'V28', 'Amount') "
                    "from the credit card fraud dataset. Human-readable fields (Transaction ID, Payment Method, IP, Location) "
                    "cannot be evaluated by this model without an upstream PCA feature-mapping pipeline. "
                    "Please use 'Test with Sample Dataset Transaction' or provide all 30 model features to run genuine ML inference."
                ),
                "missing_features_count": len(missing_features),
            }

        return None, {
            "success": False,
            "prediction": 0,
            "fraud_status": "Unavailable",
            "risk_score": 0.0,
            "verdict": "REVIEW",
            "is_mock": True,
            "error_type": "MISSING_FEATURES",
            "message": f"Request is missing {len(missing_features)} required model features: {missing_features[:5]}...",
            "missing_features": missing_features,
        }

    # Validate numerical types and absence of NaN / Infinity
    values = []
    for f in REQUIRED_FEATURES:
        val = feature_source[f]
        try:
            val_float = float(val)
        except (ValueError, TypeError):
            return None, {
                "success": False,
                "prediction": 0,
                "fraud_status": "Unavailable",
                "risk_score": 0.0,
                "verdict": "REVIEW",
                "is_mock": True,
                "error_type": "INVALID_NUMERICAL_VALUE",
                "message": f"Feature '{f}' has non-numerical value: {val!r}",
            }

        if math.isnan(val_float) or math.isinf(val_float):
            return None, {
                "success": False,
                "prediction": 0,
                "fraud_status": "Unavailable",
                "risk_score": 0.0,
                "verdict": "REVIEW",
                "is_mock": True,
                "error_type": "NUMERICAL_ANOMALY",
                "message": f"Feature '{f}' contains invalid NaN or Infinity value.",
            }

        values.append(val_float)

    # Construct single-row DataFrame with strict column order
    df_row = pd.DataFrame([values], columns=REQUIRED_FEATURES)
    return df_row, None


def predict_transaction(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute real model inference using trained artifact.
    Applies exact fitted StandardScaler to Time and Amount,
    feeds the 30-dimensional vector into XGBClassifier,
    calculates risk score and verdict, and returns structured result.
    """
    # 1. Ensure model is loaded
    loaded, err = load_model_artifact()
    if not loaded or _model is None:
        return {
            "success": False,
            "prediction": 0,
            "fraud_status": "Unavailable",
            "risk_score": 0.0,
            "verdict": "REVIEW",
            "message": f"ML model could not be loaded: {err}",
            "is_mock": True,
        }

    # 2. Extract and validate input features
    df_input, validation_error = _extract_and_validate_features(data)
    if validation_error is not None:
        return validation_error

    # 3. Apply exact preprocessing scalers (StandardScaler on Time & Amount)
    df_transformed = df_input.copy()
    raw_time = float(df_input["Time"].iloc[0])
    raw_amount = float(df_input["Amount"].iloc[0])

    if _scaler_time is not None:
        df_transformed["Time"] = _scaler_time.transform(df_input[["Time"]])
    if _scaler_amount is not None:
        df_transformed["Amount"] = _scaler_amount.transform(df_input[["Amount"]])

    # 4. Model Prediction & Probability
    try:
        # Scikit-learn XGBClassifier predict & predict_proba
        pred_array = _model.predict(df_transformed)
        prediction = int(pred_array[0])

        if hasattr(_model, "predict_proba"):
            proba_array = _model.predict_proba(df_transformed)
            # Class 1 is Fraud
            fraud_prob = float(proba_array[0][1])
        else:
            fraud_prob = float(prediction)

        risk_score = round(fraud_prob * 100.0, 2)
        fraud_status = "Fraud" if prediction == 1 else "Legitimate"

        # Determine presentation verdict
        if risk_score >= 75.0:
            verdict = "CRITICAL"
        elif risk_score >= 35.0:
            verdict = "REVIEW"
        else:
            verdict = "SAFE"

        # Construct honest evaluation message
        if prediction == 1:
            msg = (
                f"Model evaluated genuine transaction features: High probability of credit card fraud "
                f"detected (Risk Score: {risk_score}%). Note: Model outputs are statistical risk estimates, "
                f"not guaranteed financial decisions."
            )
        else:
            msg = (
                f"Model evaluated genuine transaction features: Transaction classified as Legitimate "
                f"(Risk Score: {risk_score}%). Note: Model outputs are statistical risk estimates, "
                f"not guaranteed financial decisions."
            )

        # Contextual presentation fields for UI
        tx_id = (
            data.get("transactionId")
            or data.get("query")
            or data.get("id")
            or f"TXN-{abs(hash((raw_time, raw_amount))) % 900000 + 100000}"
        )

        return {
            "success": True,
            "prediction": prediction,
            "fraud_status": fraud_status,
            "risk_score": risk_score,
            "verdict": verdict,
            "message": msg,
            "is_mock": False,
            "transactionId": str(tx_id),
            "queriedEntity": str(data.get("query") or tx_id),
            "channel": data.get("paymentMethod") or data.get("channel") or "Credit Card",
            "amount": f"${raw_amount:,.2f}",
            "rawAmount": raw_amount,
            "rawTime": raw_time,
            "recommendation": (
                "Automated Block Triggered. High-confidence fraud pattern matches trained PCA heuristics."
                if verdict == "CRITICAL"
                else (
                    "Elevated risk anomaly score. Recommend step-up 2FA verification."
                    if verdict == "REVIEW"
                    else "Low risk threshold met. Transaction cleared for settlement."
                )
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "prediction": 0,
            "fraud_status": "Unavailable",
            "risk_score": 0.0,
            "verdict": "REVIEW",
            "message": f"Inference execution failed: {str(exc)}",
            "is_mock": True,
        }