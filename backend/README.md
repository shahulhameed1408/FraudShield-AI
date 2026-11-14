# FraudShield AI — Backend & ML Documentation

Production-grade FastAPI backend and machine learning service for **FraudShield AI**, an AI-powered financial fraud detection terminal.

---

## 📌 1. Overview & Architecture

The FraudShield AI backend connects the web frontend with a trained **XGBoost Classifier** pipeline:
- **FastAPI REST API**: High-performance asynchronous API endpoints for real-time inference, health checks, audit logging, and dashboard telemetry.
- **Machine Learning Engine**: Evaluates transactions using an XGBoost model trained on the public ULB/Kaggle credit card fraud dataset (`creditcard.csv`).
- **Reproducible Preprocessing Pipeline**: Fits `StandardScaler` on `Time` and `Amount` on the training split only, uses SMOTE oversampling on training data to balance fraud instances, and evaluates on an untouched test split.
- **Persistent SQLite Audit History**: Stores transaction predictions, scores, and timestamps in `backend/data/fraudshield.db`.
- **CORS & Environment Ready**: Supports configurable CORS origins and environment variables.

---

## 📁 2. Directory Structure

```text
backend/
├── app.py                      # FastAPI REST application & routing
├── requirements.txt            # Python package dependencies
├── .env.example                # Environment variables template
├── README.md                   # This documentation guide
├── data/
│   └── fraudshield.db          # Persistent SQLite audit database
├── model/
│   ├── fraud_detection_bundle.joblib  # Bundled model, scalers, and metadata
│   ├── fraud_detection_model.pkl      # Primary serialized model artifact
│   ├── fraud_detection_model.pkl.backup # Preserved original model backup
│   └── sample_transactions.json       # Real test-split transactions for demo
└── services/
    ├── __init__.py             # Python package marker
    ├── predictor.py            # Preprocessing, validation & XGBoost inference
    └── history_db.py           # SQLite database operations & metrics aggregation
```

---

## 🛠️ 3. Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.10 – 3.14)
- `pip` package manager

### Step 1: Navigate to the Backend Directory
```bash
cd backend
```

### Step 2: (Recommended) Create a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
python -m pip install -r requirements.txt
```

---

## 🚀 4. How to Start the Backend Server

Run the following command from the `backend` folder:

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

- **Local API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc UI**: `http://127.0.0.1:8000/redoc`

---

## 🧠 5. Machine Learning Pipeline & Training

### Model Specifications
- **Algorithm**: `XGBClassifier`
- **Estimators**: 300
- **Max Depth**: 6
- **Learning Rate**: 0.1
- **Subsample**: 0.8
- **Colsample By Tree**: 0.8
- **Evaluation Metric**: `logloss`
- **Training Strategy**: Stratified 80/20 train/test split, `StandardScaler` fitted on `Time` and `Amount` on train split only, SMOTE oversampling applied on train split only.

### Evaluation Metrics on Untouched Test Split (56,962 transactions, 98 frauds)
- **Fraud Recall**: 86.73% (interception of 85 / 98 real test frauds)
- **Fraud Precision**: 72.03% (only 33 false positives out of 56,864 legitimate transactions)
- **Fraud F1-Score**: 0.7870
- **ROC-AUC**: 0.9817
- **PR-AUC (Average Precision)**: 0.8776

### Reproducing or Retraining the Model
To re-run the full training pipeline, generate updated scalers, and re-export sample transactions:
```bash
python ML/train.py
```
This script will:
1. Ingest `ML/creditcard.csv`.
2. Execute stratified splitting and fit scalers.
3. Resample using SMOTE.
4. Train XGBoost and print test metrics.
5. Export verified test rows to `backend/model/sample_transactions.json`.
6. Package model + scalers into `backend/model/fraud_detection_bundle.joblib` and update `backend/model/fraud_detection_model.pkl`.

---

## ⚠️ 6. PCA Features vs. Human Payment Details

The ULB/Kaggle dataset uses **anonymized Principal Component Analysis (PCA) features `V1`–`V28`** to preserve cardholder privacy, plus `Time` and `Amount`.

The trained model expects these **exact 30 input features in this order**:
```python
["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
```

Because human-readable fields (Transaction ID, payment gateway, IP address, geographical location) are fundamentally different from mathematical PCA embeddings, **FraudShield AI refuses to fabricate fake random PCA numbers from text**.

Instead:
1. **Option A (Preferred College Demo)**: The frontend features a **"⚡ Real Dataset Transaction"** selector that loads authentic test-set rows with all 30 features from `creditcard.csv` to run genuine XGBoost inference (`is_mock: false`).
2. **Human Checker Validation**: Submitting human fields without the 30 PCA features returns an honest explanation of the PCA requirement (`success: false, is_mock: true`) rather than a misleading fake prediction.

---

## 📡 7. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Confirms backend service is running. |
| `GET` | `/health` | Diagnostic check for model and scaler readiness. |
| `GET` | `/sample-transactions` | Authentic test rows for genuine demonstration. |
| `POST` | `/predict` | Evaluates a transaction vector and returns fraud prediction + risk score. |
| `GET` | `/history` | Retrieves saved audit records from SQLite (supports `limit`, `status`, `search`). |
| `GET` | `/history/{id}` | Retrieves full details of a specific analysis record. |
| `DELETE` | `/history/{id}` | Deletes an analysis record from persistent history. |
| `GET` | `/dashboard/kpis` | Aggregated metrics calculated from SQLite database. |
| `GET` | `/analytics/chart` | Attack trend volume by timeframe (`24h`, `7d`, `30d`). |
| `GET` | `/transactions/feed` | Recent transaction feed for dashboard. |

### Sample cURL Requests

#### 1. Evaluate a Genuine Transaction Vector (30 Features)
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "TXN-TEST-1",
       "amount": 23.00,
       "features": {
         "Time": 160760.0,
         "V1": -0.6744, "V2": 1.4081, "V3": -1.1106, "V4": -1.3283,
         "V5": 1.3889, "V6": -1.3084, "V7": 1.8858, "V8": -0.6142,
         "V9": 0.3116, "V10": 0.6507, "V11": -0.8577, "V12": -0.2299,
         "V13": -0.1998, "V14": 0.2663, "V15": -0.0465, "V16": -0.7413,
         "V17": -0.6056, "V18": -0.3925, "V19": -0.1626, "V20": 0.3943,
         "V21": 0.0800, "V22": 0.8100, "V23": -0.2243, "V24": 0.7078,
         "V25": -0.1358, "V26": 0.0451, "V27": 0.5338, "V28": 0.2913,
         "Amount": 23.00
       }
     }'
```

#### Response (Legitimate):
```json
{
  "success": true,
  "prediction": 0,
  "fraud_status": "Legitimate",
  "risk_score": 0.0,
  "verdict": "SAFE",
  "message": "Model evaluated genuine transaction features: Transaction classified as Legitimate (Risk Score: 0.0%).",
  "is_mock": false,
  "transactionId": "TXN-TEST-1"
}
```

---

## 🌐 8. Deployment Requirements

1. **Frontend**: Static files (`index.html`, `css/`, `js/`) can be hosted on GitHub Pages, Vercel, Netlify, or Firebase Hosting. Update `js/config.js` or define `window.__FRAUDSHIELD_API_URL__` with the deployed backend URL.
2. **Backend**: Host with an ASGI server (`uvicorn` or `gunicorn` with uvicorn workers) on Render, Railway, AWS EC2/ECS, or Google Cloud Run.
3. **Model Artifact**: Ensure `backend/model/fraud_detection_bundle.joblib` or `fraud_detection_model.pkl` is bundled in the container / virtualenv.
4. **Environment Variables**: Configure `ALLOWED_ORIGINS` to permit the production frontend origin domain.
