"""
FraudShield AI - Reproducible Model Training & Preprocessing Pipeline
=====================================================================
Loads creditcard.csv, performs stratified train/test split, fits
StandardScaler on Time & Amount (training data only), applies SMOTE
only on the training split, trains XGBClassifier (300 estimators, max depth 6),
evaluates comprehensively on the untouched test split, extracts sample transactions
for the frontend/API demonstration, and packages the model & scalers together into a versioned artifact.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DATA_PATH = CURRENT_DIR / "creditcard.csv"
MODEL_DIR = PROJECT_ROOT / "backend" / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

BUNDLE_OUTPUT_PATH = MODEL_DIR / "fraud_detection_bundle.joblib"
PKL_OUTPUT_PATH = MODEL_DIR / "fraud_detection_model.pkl"
SAMPLE_TX_PATH = MODEL_DIR / "sample_transactions.json"


def run_training():
    print("=" * 70)
    print("FRAUDSHIELD AI - MODEL TRAINING PIPELINE")
    print("=" * 70)

    # 1. Load Dataset
    print(f"\n[1/7] Loading dataset from: {DATA_PATH}")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"      Dataset loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")

    # Verify column presence
    feature_cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
    if not all(col in df.columns for col in feature_cols + ["Class"]):
        raise ValueError("Dataset is missing expected columns.")

    class_counts = df["Class"].value_counts().to_dict()
    print(f"      Class distribution: Legitimate (0): {class_counts.get(0, 0):,}, Fraud (1): {class_counts.get(1, 0):,}")
    fraud_pct = (class_counts.get(1, 0) / len(df)) * 100
    print(f"      Fraud percentage: {fraud_pct:.4f}%")

    # 2. Stratified Train / Test Split
    print("\n[2/7] Splitting data into Train (80%) and Test (20%) with stratification...")
    X = df[feature_cols].copy()
    y = df["Class"].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"      Train set size: {X_train.shape[0]:,} samples (Frauds: {y_train.sum():,})")
    print(f"      Test set size:  {X_test.shape[0]:,} samples (Frauds: {y_test.sum():,})")

    # 3. Preprocessing: Fit StandardScaler on Time and Amount on Train split ONLY
    print("\n[3/7] Fitting StandardScaler on 'Time' and 'Amount' (Train set only)...")
    scaler_time = StandardScaler()
    scaler_amount = StandardScaler()

    scaler_time.fit(X_train[["Time"]])
    scaler_amount.fit(X_train[["Amount"]])

    # Apply scaling to Train and Test sets
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()

    X_train_scaled["Time"] = scaler_time.transform(X_train[["Time"]])
    X_train_scaled["Amount"] = scaler_amount.transform(X_train[["Amount"]])

    X_test_scaled["Time"] = scaler_time.transform(X_test[["Time"]])
    X_test_scaled["Amount"] = scaler_amount.transform(X_test[["Amount"]])

    # 4. Apply SMOTE to Training Split ONLY
    print("\n[4/7] Applying SMOTE oversampling to training set only...")
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
    print(f"      After SMOTE: {X_train_resampled.shape[0]:,} training samples")
    print(f"      Balanced class counts: 0={sum(y_train_resampled == 0):,}, 1={sum(y_train_resampled == 1):,}")

    # 5. Train XGBClassifier
    print("\n[5/7] Training XGBClassifier with specified hyperparameters...")
    print("      - n_estimators=300")
    print("      - max_depth=6")
    print("      - learning_rate=0.1")
    print("      - subsample=0.8")
    print("      - colsample_bytree=0.8")
    print("      - random_state=42")
    print("      - eval_metric='logloss'")

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1,
    )

    t0 = time.time()
    model.fit(X_train_resampled, y_train_resampled)
    train_duration = time.time() - t0
    print(f"      Training completed in {train_duration:.2f} seconds.")

    # 6. Comprehensive Evaluation on Untouched Test Split
    print("\n[6/7] Evaluating model on untouched Test Split...")
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    print("\n--- TEST METRICS REPORT ---")
    print(f"Confusion Matrix:\n{cm}")
    tn, fp, fn, tp = cm.ravel()
    print(f"True Negatives:  {tn:,} | False Positives: {fp:,}")
    print(f"False Negatives: {fn:,} | True Positives:  {tp:,}")
    print("-" * 35)
    print(f"Precision:         {prec:.4f}")
    print(f"Recall:            {rec:.4f}")
    print(f"F1-Score:          {f1:.4f}")
    print(f"ROC-AUC:           {roc_auc:.4f}")
    print(f"PR-AUC (Avg Prec): {pr_auc:.4f}")
    print("-" * 35)
    print("\nClassification Report:\n", classification_report(y_test, y_pred, digits=4))

    # 7. Extract Real Sample Dataset Transactions for Demo & Testing
    print("\n[7/7] Extracting real sample dataset rows for demo & testing...")
    # Get 5 legitimate and 5 fraud rows from test set (using original unscaled values so user can see real Time/Amount)
    test_indices_legit = y_test[y_test == 0].index[:5]
    test_indices_fraud = y_test[y_test == 1].index[:5]

    samples = []

    for idx in test_indices_legit:
        raw_row = df.loc[idx]
        features_dict = {col: float(raw_row[col]) for col in feature_cols}
        prob = float(y_prob[X_test_scaled.index.get_loc(idx)])
        pred = int(y_pred[X_test_scaled.index.get_loc(idx)])
        samples.append({
            "id": f"DATASET-ROW-{idx}",
            "description": f"Legitimate Transaction (Test Set #{idx})",
            "ground_truth": 0,
            "ground_truth_label": "Legitimate",
            "expected_prediction": pred,
            "expected_risk_score": round(prob * 100, 2),
            "time_raw": float(raw_row["Time"]),
            "amount_raw": float(raw_row["Amount"]),
            "features": features_dict,
        })

    for idx in test_indices_fraud:
        raw_row = df.loc[idx]
        features_dict = {col: float(raw_row[col]) for col in feature_cols}
        prob = float(y_prob[X_test_scaled.index.get_loc(idx)])
        pred = int(y_pred[X_test_scaled.index.get_loc(idx)])
        samples.append({
            "id": f"DATASET-ROW-{idx}",
            "description": f"Fraudulent Transaction (Test Set #{idx})",
            "ground_truth": 1,
            "ground_truth_label": "Fraud",
            "expected_prediction": pred,
            "expected_risk_score": round(prob * 100, 2),
            "time_raw": float(raw_row["Time"]),
            "amount_raw": float(raw_row["Amount"]),
            "features": features_dict,
        })

    with open(SAMPLE_TX_PATH, "w") as f:
        json.dump(samples, f, indent=2)
    print(f"      Saved {len(samples)} real sample transactions to: {SAMPLE_TX_PATH}")

    # Build Versioned Artifact Bundle
    artifact_bundle = {
        "model": model,
        "scaler_time": scaler_time,
        "scaler_amount": scaler_amount,
        "feature_names": feature_cols,
        "metrics": {
            "confusion_matrix": cm.tolist(),
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_version": "v1.0.0-xgb-smote-scaled",
        "description": "XGBClassifier trained on creditcard.csv with StandardScaler for Time/Amount and SMOTE",
    }

    print(f"\n      Saving artifact bundle to: {BUNDLE_OUTPUT_PATH}")
    joblib.dump(artifact_bundle, BUNDLE_OUTPUT_PATH, compress=3)

    print(f"      Updating primary model artifact at: {PKL_OUTPUT_PATH}")
    joblib.dump(artifact_bundle, PKL_OUTPUT_PATH, compress=3)

    print("\n" + "=" * 70)
    print("TRAINING & ARTIFACT PACKAGING SUCCESSFUL!")
    print("=" * 70)


if __name__ == "__main__":
    run_training()
