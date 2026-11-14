"""
FraudShield AI - Automated Comprehensive Test Suite
===================================================
Tests all 12 verification criteria specified in requirements:
1. Backend imports and startup
2. Model artifact loading
3. Health endpoint readiness
4. Valid model-feature input (Legitimate & Fraud)
5. Missing feature rejection / transparent PCA explanation
6. Invalid numerical input rejection (NaN / string)
7. Actual prediction and probability generation (verify is_mock == False)
8. Prediction response schema validation
9. Persistent SQLite history creation, retrieval, and deletion
10. Sample transactions API availability
11. Dashboard KPI aggregation from history
12. Complete full-cycle transaction analysis
"""

import math
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app import app
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
    save_prediction_record,
)


class TestFraudShieldBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.samples = get_sample_transactions()

    # 1. Backend imports and startup
    def test_01_backend_imports_and_startup(self):
        self.assertIsNotNone(app)
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "online")

    # 2. Model artifact loading
    def test_02_model_artifact_loading(self):
        self.assertTrue(is_model_loaded(), "XGBoost model should be loaded successfully.")
        self.assertTrue(is_preprocessing_ready(), "StandardScaler objects must be ready.")
        status = get_model_status()
        self.assertIn("v1.0.0", status["metadata"].get("version", ""))

    # 3. Health endpoint
    def test_03_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "healthy")
        self.assertTrue(body["model_loaded"])
        self.assertTrue(body["preprocessing_ready"])
        self.assertEqual(body["engine_mode"], "trained_xgboost")

    # 4. Valid model-feature input: Legitimate transaction
    def test_04_valid_legitimate_input(self):
        legit_sample = next((s for s in self.samples if s["ground_truth"] == 0), None)
        self.assertIsNotNone(legit_sample, "Sample transactions must contain legitimate cases.")

        payload = {
            "query": legit_sample["id"],
            "amount": legit_sample["amount_raw"],
            "features": legit_sample["features"],
        }
        res = self.client.post("/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["is_mock"], "Genuine inference must set is_mock to False.")
        self.assertEqual(data["prediction"], 0)
        self.assertEqual(data["fraud_status"], "Legitimate")
        self.assertLessEqual(data["risk_score"], 35.0)

    # 5. Valid model-feature input: Fraudulent transaction
    def test_05_valid_fraud_input(self):
        fraud_sample = next((s for s in self.samples if s["ground_truth"] == 1), None)
        self.assertIsNotNone(fraud_sample, "Sample transactions must contain fraud cases.")

        payload = {
            "query": fraud_sample["id"],
            "amount": fraud_sample["amount_raw"],
            "features": fraud_sample["features"],
        }
        res = self.client.post("/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["is_mock"], "Genuine inference must set is_mock to False.")
        self.assertEqual(data["prediction"], 1)
        self.assertEqual(data["fraud_status"], "Fraud")
        self.assertGreaterEqual(data["risk_score"], 75.0)

    # 6. Missing feature rejection & PCA mismatch explanation
    def test_06_missing_feature_rejection(self):
        # Sending human-readable fields only
        human_payload = {
            "query": "TXN-SAMPLE-100",
            "amount": 250.0,
            "paymentMethod": "Credit Card",
            "userLocation": "California, US",
        }
        res = self.client.post("/predict", json=human_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Honest response: model cannot score without PCA features
        self.assertFalse(data["success"])
        self.assertTrue(data["is_mock"])
        self.assertIn("PCA features", data["message"])

    # 7. Invalid numerical input rejection
    def test_07_invalid_numerical_input_rejection(self):
        legit_sample = self.samples[0]
        corrupted_features = dict(legit_sample["features"])
        corrupted_features["V1"] = "invalid_string_val"

        result = predict_transaction({"features": corrupted_features})
        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "INVALID_NUMERICAL_VALUE")

        # Test NaN rejection
        corrupted_features["V1"] = float("nan")
        result_nan = predict_transaction({"features": corrupted_features})
        self.assertFalse(result_nan["success"])
        self.assertEqual(result_nan["error_type"], "NUMERICAL_ANOMALY")

    # 8. Prediction response schema
    def test_08_prediction_response_schema(self):
        legit_sample = self.samples[0]
        res = self.client.post(
            "/predict",
            json={
                "query": legit_sample["id"],
                "amount": legit_sample["amount_raw"],
                "features": legit_sample["features"],
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        required_keys = {"success", "prediction", "fraud_status", "risk_score", "message", "is_mock", "verdict", "transactionId"}
        self.assertTrue(required_keys.issubset(data.keys()), f"Missing keys in {data.keys()}")

    # 9. Persistent SQLite history creation, retrieval, and deletion
    def test_09_persistent_history_lifecycle(self):
        test_id = f"TEST-TX-{int(os.getpid())}"
        rec_id = save_prediction_record({
            "transaction_id": test_id,
            "entity": "unit_test_user@example.com",
            "channel": "Credit Card",
            "amount": 199.99,
            "prediction": 0,
            "fraud_status": "Legitimate",
            "risk_score": 5.4,
            "verdict": "SAFE",
            "message": "Unit test verified.",
            "is_mock": False,
        })
        self.assertIsInstance(rec_id, int)

        # Retrieve single
        retrieved = get_history_by_id(rec_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["transactionId"], test_id)

        # Retrieve list via endpoint
        res = self.client.get(f"/history?search={test_id}")
        self.assertEqual(res.status_code, 200)
        history_list = res.json()["history"]
        self.assertTrue(any(h["transactionId"] == test_id for h in history_list))

        # Delete
        del_res = self.client.delete(f"/history/{rec_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertIsNone(get_history_by_id(rec_id))

    # 10. Dashboard KPI metrics calculation
    def test_10_dashboard_kpis(self):
        res = self.client.get("/dashboard/kpis")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("totalScanned", data)
        self.assertIn("blockedAttempts", data)
        self.assertIn("currentRiskIndex", data)
        self.assertIn("aiEfficiency", data)

    # 11. Sample transactions endpoint
    def test_11_sample_transactions_endpoint(self):
        res = self.client.get("/sample-transactions")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["count"], 0)
        first_sample = data["samples"][0]
        self.assertEqual(len(first_sample["features"]), 30)

    # 12. Full cycle transaction analysis through endpoint
    def test_12_full_cycle_analysis(self):
        fraud_sample = next((s for s in self.samples if s["ground_truth"] == 1), None)
        self.assertIsNotNone(fraud_sample)

        res = self.client.post("/predict", json={
            "query": "FULL-CYCLE-AUDIT-101",
            "amount": fraud_sample["amount_raw"],
            "features": fraud_sample["features"],
        })
        self.assertEqual(res.status_code, 200)
        result = res.json()
        self.assertTrue(result["success"])
        self.assertFalse(result["is_mock"])
        self.assertEqual(result["prediction"], 1)
        self.assertIn("historyId", result)

        # Verify it was persisted to SQLite
        saved = get_history_by_id(result["historyId"])
        self.assertIsNotNone(saved)
        self.assertEqual(saved["transactionId"], "FULL-CYCLE-AUDIT-101")


if __name__ == "__main__":
    unittest.main(verbosity=2)
