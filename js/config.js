/**
 * FraudShield AI - Configuration Settings
 * Dynamic and environment-aware configuration for API endpoints,
 * risk thresholds, and workspace metadata.
 */



const getInitialBaseUrl = () => {
  if (typeof window === 'undefined') {
    return 'http://localhost:8000';
  }

  // Runtime global override
  if (window.__FRAUDSHIELD_API_URL__) {
    return window.__FRAUDSHIELD_API_URL__;
  }

  // Check localStorage override
  const stored = localStorage.getItem('fraudshield_api_url');
  if (stored) {
    return stored.replace(/\/+$/, '');
  }

  const hostname = window.location.hostname;
  const isLocalhost =
    hostname === 'localhost' || hostname === '127.0.0.1';

  // Production backend on Render
  if (!isLocalhost) {
    return 'https://fraudshield-ai-g53h.onrender.com';
  }

  // Local development backend
  return 'http://localhost:8000';
};

export const CONFIG = {
  // Backend API Base URL
  API_BASE_URL: getInitialBaseUrl(),

  // Network timeout (milliseconds)
  TIMEOUT_MS: 10000,

  // Risk Score Thresholds
  THRESHOLDS: {
    SAFE_MAX: 34,
    REVIEW_MAX: 74,
    CRITICAL_MIN: 75
  },

  // Workspace Metadata
  SYSTEM: {
    NAME: 'FraudShield AI',
    VERSION: 'v2.4-Neural',
    ENGINE_STATUS: 'ONLINE',
    MODEL_ID: 'fs-xgboost-smote-v1'
  },

  // Update API URL at runtime
  setApiBaseUrl(newUrl) {
    if (!newUrl) return;

    this.API_BASE_URL = newUrl.replace(/\/+$/, '');

    try {
      localStorage.setItem(
        'fraudshield_api_url',
        this.API_BASE_URL
      );
    } catch (e) {
      console.warn(
        'Could not persist API_BASE_URL to localStorage',
        e
      );
    }
  }
};
