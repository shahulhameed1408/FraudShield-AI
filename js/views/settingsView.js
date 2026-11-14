/**
 * FraudShield AI - System Settings View Controller
 */

import { CONFIG } from '../config.js';
import { toast } from '../toast.js';

export class SettingsView {
  constructor(router) {
    this.router = router;
  }

  init() {
    const urlInput = document.getElementById('settings-api-url');
    if (urlInput) {
      urlInput.value = CONFIG.API_BASE_URL;
    }

    const testBtn = document.getElementById('settings-test-api-btn');
    if (testBtn) {
      testBtn.addEventListener('click', async () => {
        testBtn.disabled = true;
        testBtn.textContent = 'CONNECTING...';

        try {
          const testBase = urlInput.value.replace(/\/+$/, '');
          const res = await fetch(`${testBase}/health`, { method: 'GET' });
          if (res.ok) {
            const data = await res.json();
            const mode = data.model_loaded ? 'XGBoost Active' : 'Standby';
            toast.show({
              title: 'Backend Online',
              message: `Handshake successful (${mode}, 30-feature pipeline ready).`,
              type: 'safe'
            });
          } else {
            throw new Error(`Status ${res.status}`);
          }
        } catch (err) {
          toast.show({
            title: 'Backend Connection Failed',
            message: `Could not reach ${urlInput.value}. Ensure FastAPI is running with 'python -m uvicorn app:app --reload'.`,
            type: 'critical'
          });
        } finally {
          testBtn.disabled = false;
          testBtn.textContent = 'TEST CONNECTION';
        }
      });
    }

    const saveBtn = document.getElementById('settings-save-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        CONFIG.setApiBaseUrl(urlInput.value);
        toast.show({
          title: 'Configuration Saved',
          message: `Backend API route updated to ${CONFIG.API_BASE_URL}.`,
          type: 'safe'
        });
      });
    }
  }
}
