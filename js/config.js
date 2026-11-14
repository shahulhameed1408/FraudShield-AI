/**
 * FraudShield AI - Configuration Settings
 * Dynamic and environment-aware configuration for API endpoints,
 * risk thresholds, and workspace metadata.
 */

const getInitialBaseUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:8000';

  // 1. Check runtime global injection (e.g. from container or env script)
  if (window.__FRAUDSHIELD_API_URL__) return window.__FRAUDSHIELD_API_URL__;

  // 2. Check localStorage override (configured via Settings view)
  const stored = localStorage.getItem('fraudshield_api_url');
  if (stored) return stored;

  const hostname = window.location.hostname;
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

  // 3. In production (e.g. Hugging Face Spaces *.hf.space, custom domains, or public IP):
  // Frontend and backend are served from the same origin
  if (!isLocalhost && window.location.origin) {
    return window.location.origin;
  }

  // 4. Local development:
  // If running on a dedicated frontend dev server (e.g. python -m http.server 3000 or Live Server 5500),
  // route requests to the standalone FastAPI backend at http://localhost:8000
  const port = window.location.port;
  if (port === '3000' || port === '5500' || port === '5173') {
    return 'http://localhost:8000';
  }

  // If running unified locally on any port (e.g. :7860 or :8000), use the current origin
  if (window.location.origin) {
    return window.location.origin;
  }

  return 'http://localhost:8000';
};

export const CONFIG = {
  // Backend API Base URL (configurable at runtime via Settings)
  API_BASE_URL: getInitialBaseUrl(),

  // Timeout for network calls (in milliseconds)
  TIMEOUT_MS: 10000,

  // Risk Score Thresholds (0 - 100 Scale)
  THRESHOLDS: {
    SAFE_MAX: 34,      // 0 - 34: Safe / Clean Check
    REVIEW_MAX: 74,    // 35 - 74: Elevated / Manual Review
    CRITICAL_MIN: 75   // 75 - 100: Critical Fraud Blocked
  },

  // Workspace Metadata
  SYSTEM: {
    NAME: 'FraudShield AI',
    VERSION: 'v2.4-Neural',
    ENGINE_STATUS: 'ONLINE',
    MODEL_ID: 'fs-xgboost-smote-v1'
  },

  setApiBaseUrl(newUrl) {
    if (!newUrl) return;
    this.API_BASE_URL = newUrl.replace(/\/+$/, '');
    try {
      localStorage.setItem('fraudshield_api_url', this.API_BASE_URL);
    } catch (e) {
      console.warn('Could not persist API_BASE_URL to localStorage', e);
    }
  }
};
