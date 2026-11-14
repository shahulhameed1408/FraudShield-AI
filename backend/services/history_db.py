"""
FraudShield AI - SQLite Persistent Demo History Service
======================================================
Stores and retrieves transaction analysis records, audit history,
and aggregated metrics for the dashboard.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

CURRENT_DIR = Path(__file__).resolve().parent
DATA_DIR = CURRENT_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "fraudshield.db"


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield an open SQLite connection and ensure it is properly closed."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database tables and seed baseline records if empty."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                entity TEXT,
                channel TEXT,
                amount REAL,
                currency TEXT DEFAULT 'USD',
                prediction INTEGER NOT NULL,
                fraud_status TEXT NOT NULL,
                risk_score REAL NOT NULL,
                verdict TEXT NOT NULL,
                message TEXT,
                is_mock INTEGER NOT NULL DEFAULT 0,
                ip_address TEXT,
                user_location TEXT,
                features_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

        # Check if table is empty, seed initial realistic records
        cursor.execute("SELECT COUNT(*) FROM analysis_history")
        count = cursor.fetchone()[0]

        if count == 0:
            seed_records = [
                (
                    "TXN-98420",
                    "user_49102@proton.me",
                    "Wire Transfer",
                    4850.00,
                    "USD",
                    1,
                    "Fraud",
                    94.2,
                    "CRITICAL",
                    "Flagged high-risk transaction: Tor Exit Node & Velocity Spikes.",
                    0,
                    "185.220.101.5",
                    "Netherlands (Tor)",
                    "2026-09-24T00:08:12Z",
                ),
                (
                    "TXN-98419",
                    "0x89C4...2E1F",
                    "Web3 Gateway",
                    120.00,
                    "USD",
                    0,
                    "Legitimate",
                    12.4,
                    "SAFE",
                    "Verified smart contract interaction within standard parameters.",
                    0,
                    "73.189.44.12",
                    "California, US",
                    "2026-09-24T00:07:44Z",
                ),
                (
                    "TXN-98418",
                    "sarah.k@retailer.com",
                    "Credit Card",
                    890.50,
                    "USD",
                    0,
                    "Legitimate",
                    58.0,
                    "REVIEW",
                    "Elevated risk score due to hardware signature change. Review advised.",
                    0,
                    "142.250.190.46",
                    "New York, US",
                    "2026-09-24T00:06:19Z",
                ),
                (
                    "TXN-98416",
                    "0x43F1...90AB",
                    "Smart Contract",
                    12400.00,
                    "USD",
                    1,
                    "Fraud",
                    88.6,
                    "CRITICAL",
                    "Sanctioned wallet interaction pattern detected.",
                    0,
                    "198.51.100.22",
                    "Unknown / Proxy",
                    "2026-09-24T00:04:55Z",
                ),
                (
                    "TXN-98415",
                    "alex.m@domain.co.uk",
                    "Debit Card",
                    64.99,
                    "USD",
                    0,
                    "Legitimate",
                    8.8,
                    "SAFE",
                    "Consistent billing coordinates and low-risk transaction amount.",
                    0,
                    "82.165.197.1",
                    "London, UK",
                    "2026-09-24T00:02:10Z",
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO analysis_history (
                    transaction_id, entity, channel, amount, currency,
                    prediction, fraud_status, risk_score, verdict,
                    message, is_mock, ip_address, user_location, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                seed_records,
            )
            conn.commit()


def save_prediction_record(data: Dict[str, Any]) -> int:
    """Save a prediction result into persistent SQLite history."""
    init_db()

    features_json = None
    if "features" in data and isinstance(data["features"], dict):
        try:
            features_json = json.dumps(data["features"])
        except Exception:
            features_json = None

    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_history (
                transaction_id, entity, channel, amount, currency,
                prediction, fraud_status, risk_score, verdict,
                message, is_mock, ip_address, user_location, features_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("transaction_id") or data.get("transactionId") or "TXN-AUTO",
                data.get("entity") or data.get("queriedEntity") or "N/A",
                data.get("channel") or data.get("paymentMethod") or "Credit Card",
                float(data.get("amount") or 0.0),
                data.get("currency") or "USD",
                int(data.get("prediction", 0)),
                data.get("fraud_status", "Legitimate"),
                float(data.get("risk_score", 0.0)),
                data.get("verdict", "SAFE"),
                data.get("message", ""),
                1 if data.get("is_mock", False) else 0,
                data.get("ip_address") or data.get("ipAddress"),
                data.get("user_location") or data.get("userLocation"),
                features_json,
                now_iso,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_all_history(
    limit: int = 100,
    filter_status: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve history records ordered by creation date descending."""
    init_db()

    query = "SELECT * FROM analysis_history WHERE 1=1"
    params: List[Any] = []

    if filter_status and filter_status != "ALL":
        query += " AND verdict = ?"
        params.append(filter_status)

    if search:
        query += (
            " AND (transaction_id LIKE ? OR entity LIKE ? OR channel LIKE ? OR message LIKE ?)"
        )
        term = f"%{search}%"
        params.extend([term, term, term, term])

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "transactionId": r["transaction_id"],
                "entity": r["entity"] or r["transaction_id"],
                "channel": r["channel"],
                "amount": f"${r['amount']:,.2f}" if r["amount"] is not None else "$0.00",
                "rawAmount": r["amount"],
                "currency": r["currency"],
                "prediction": r["prediction"],
                "fraudStatus": r["fraud_status"],
                "riskScore": r["risk_score"],
                "verdict": r["verdict"],
                "message": r["message"],
                "isMock": bool(r["is_mock"]),
                "ipAddress": r["ip_address"],
                "userLocation": r["user_location"],
                "timestamp": r["created_at"],
            })
        return results


def get_history_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single history record by ID."""
    init_db()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_history WHERE id = ?", (record_id,))
        r = cursor.fetchone()
        if not r:
            return None

        features = None
        if r["features_json"]:
            try:
                features = json.loads(r["features_json"])
            except Exception:
                features = None

        return {
            "id": r["id"],
            "transactionId": r["transaction_id"],
            "entity": r["entity"],
            "channel": r["channel"],
            "amount": f"${r['amount']:,.2f}" if r["amount"] is not None else "$0.00",
            "rawAmount": r["amount"],
            "currency": r["currency"],
            "prediction": r["prediction"],
            "fraudStatus": r["fraud_status"],
            "riskScore": r["risk_score"],
            "verdict": r["verdict"],
            "message": r["message"],
            "isMock": bool(r["is_mock"]),
            "ipAddress": r["ip_address"],
            "userLocation": r["user_location"],
            "features": features,
            "timestamp": r["created_at"],
        }


def delete_history_by_id(record_id: int) -> bool:
    """Delete a history record by ID."""
    init_db()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analysis_history WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_dashboard_metrics() -> Dict[str, Any]:
    """Calculate live metrics from history database."""
    init_db()

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM analysis_history")
        total_scanned = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM analysis_history WHERE prediction = 1")
        blocked_attempts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM analysis_history WHERE prediction = 0")
        legitimate_count = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(risk_score) FROM analysis_history")
        avg_risk = cursor.fetchone()[0]
        avg_risk = round(float(avg_risk), 1) if avg_risk is not None else 18.0

        efficiency = (
            round((legitimate_count / total_scanned) * 100, 1)
            if total_scanned > 0
            else 99.4
        )

        return {
            "totalScanned": total_scanned,
            "blockedAttempts": blocked_attempts,
            "legitimateCount": legitimate_count,
            "currentRiskIndex": int(avg_risk),
            "riskStatus": "LOW_THREAT" if avg_risk < 35 else ("ELEVATED" if avg_risk < 75 else "HIGH_THREAT"),
            "aiEfficiency": f"{efficiency}%",
            "efficiencyTrend": "+0.2%",
        }


# Initialize DB on module import
init_db()
