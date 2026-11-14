# FraudShield AI — Autonomous Financial Fraud Detection System

**FraudShield AI** is a full-stack, AI-driven financial fraud detection website and REST API built for academic demonstration, technical presentation, and viva evaluation.

The system combines an **HTML5/CSS3/ES6 Vanilla JS Single-Page Workspace** with a high-performance **FastAPI backend** and an **XGBoost machine learning classifier** trained on authentic credit card transaction data.

---

## 🌟 Key Features

1. **Authentic XGBoost Machine Learning Engine**:
   - 30-feature vector inference trained on `creditcard.csv`.
   - `StandardScaler` normalization fitted on `Time` and `Amount` on train split only.
   - SMOTE balanced oversampling on training data.
   - Genuine probability scores (0.0% to 100.0%) and prediction classes (`0` = Legitimate, `1` = Fraud).
   - Zero fabricated numbers (`is_mock: false`).

2. **Option A Demonstration Mode**:
   - One-click testing with authentic test-set transactions from `creditcard.csv`.
   - Inspection of all 30 PCA features.
   - Clear diagnostic feedback when submitting human-readable payment details.

3. **Persistent SQLite Audit History**:
   - Saves every evaluated transaction to `backend/data/fraudshield.db`.
   - History viewer with search, filtering by threat level, and record deletion.

4. **Real-Time Analytics Dashboard**:
   - Aggregated KPIs (Total Scanned, Blocked Attempts, Current Risk Index, AI Efficiency Rate).
   - Interactive SVG attack trend charts (24H, 7D, 30D).
   - Live transaction feed connected to SQLite records.

---

## 📁 Project Architecture

```text
AI Fraud Detection/
├── index.html              # Main application shell with persistent sidebar and topbar
├── dashboard.html          # Shortcut redirect to Analytics Dashboard
├── checker.html            # Shortcut redirect to Transaction Risk Scanner
├── result.html             # Shortcut redirect to Deep Scan Result
├── history.html            # Shortcut redirect to Alerts Log & History
├── css/                    # Theme, layout, animations, components, view styles
├── js/
│   ├── config.js           # Dynamic environment configuration
│   ├── api.js              # Centralized API service layer
│   ├── router.js           # Single-page application route controller
│   ├── app.js              # Application entrypoint & live health status
│   ├── components/         # Matrix text scrambler, risk score gauge, attack chart
│   └── views/              # Controllers for Dashboard, Scanner, Result, Alerts, Settings
├── ML/
│   ├── creditcard.csv      # Anonymized ULB/Kaggle credit card fraud dataset
│   ├── eda.py              # Exploratory data analysis script
│   └── train.py            # Reproducible model training & packaging pipeline
└── backend/
    ├── app.py              # FastAPI application & REST endpoints
    ├── requirements.txt    # Python backend dependencies
    ├── .env.example        # Environment variable template
    ├── README.md           # Backend and ML detailed documentation
    ├── data/
    │   └── fraudshield.db  # Persistent SQLite database
    ├── model/
    │   ├── fraud_detection_bundle.joblib  # Model + scalers artifact
    │   ├── fraud_detection_model.pkl      # Serialized artifact bundle
    │   └── sample_transactions.json       # Extracted test dataset rows
    └── services/
        ├── predictor.py    # Preprocessing & XGBoost inference service
        └── history_db.py   # SQLite persistence & KPI aggregation
```

---

## 🚀 How to Run the Complete Project

### 1. Start the FastAPI Backend
Open a terminal in the project root:
```bash
cd backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Swagger Docs: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend Website
Open a second terminal in the project root:
```bash
python -m http.server 3000
```
- Open `http://localhost:3000` in your web browser.
- Alternatively, if using VS Code, right-click `index.html` and select **"Open with Live Server"**.

---

## 🧪 Model Performance Metrics (Untouched Test Split)

- **Test Samples**: 56,962 transactions (98 true frauds)
- **Fraud Recall**: **86.73%** (85 / 98 fraud cases blocked)
- **Fraud Precision**: **72.03%**
- **F1-Score**: **0.7870**
- **ROC-AUC**: **0.9817**
- **PR-AUC (Average Precision)**: **0.8776**

---

## 📖 Presentation / College Viva Tips

- **PCA Feature Explanation**: Explain to the examiner that the Kaggle/ULB dataset anonymized features `V1`–`V28` using Principal Component Analysis to protect user privacy. FraudShield AI transparently demonstrates genuine ML inference on those 30 mathematical components (Option A) rather than generating fake numbers from card numbers or names.
- **Preprocessing Pipeline**: Highlight that `StandardScaler` for `Time` and `Amount` was fit strictly on the training set to prevent data leakage, and SMOTE was applied solely to the training split.
- **Audit Persistence**: Show that running a transaction in the Scanner immediately updates the **Alerts Log** (`history.html`) and live metrics on the **Dashboard** (`dashboard.html`) via SQLite.
