/**
 * FraudShield AI - Transaction Checker (Deep Scan Tool) View Controller (Page 2)
 * Supports Option A (Authentic ML Model inference using creditcard.csv test rows)
 * and transparent human-form validation testing.
 */

import { api } from '../api.js';
import { scrambleText } from '../components/matrixText.js';
import { toast } from '../toast.js';

export class CheckerView {
  constructor(router) {
    this.router = router;

    // Elements for Sample Mode (Option A)
    this.tabSample = null;
    this.tabCustom = null;
    this.panelSample = null;
    this.panelCustom = null;
    this.sampleSelect = null;
    this.btnRunSample = null;
    this.sampleFeaturesGrid = null;
    this.samples = [];
    this.selectedSample = null;

    // Elements for Custom/Human Mode
    this.inputElement = null;
    this.detectPill = null;
    this.detectIcon = null;
    this.detectText = null;
    this.scanBtn = null;
    this.advancedToggle = null;
    this.advancedGrid = null;
    this.currentQueryType = 'TX_ID';
    this.isScanning = false;
  }

  async init() {
    // 1. Grab DOM references
    this.tabSample = document.getElementById('tab-sample-mode');
    this.tabCustom = document.getElementById('tab-custom-mode');
    this.panelSample = document.getElementById('panel-sample-mode');
    this.panelCustom = document.getElementById('panel-custom-mode');
    this.sampleSelect = document.getElementById('sample-row-select');
    this.btnRunSample = document.getElementById('btn-run-sample-scan');
    this.sampleFeaturesGrid = document.getElementById('sample-features-grid');

    this.inputElement = document.getElementById('scan-entity-input');
    this.detectPill = document.getElementById('scan-detect-pill');
    this.detectIcon = document.getElementById('scan-detect-icon');
    this.detectText = document.getElementById('scan-detect-text');
    this.scanBtn = document.getElementById('scan-action-btn');
    this.advancedToggle = document.getElementById('advanced-toggle-btn');
    this.advancedGrid = document.getElementById('advanced-params-grid');

    // 2. Mode Toggle Tabs
    if (this.tabSample && this.tabCustom) {
      this.tabSample.addEventListener('click', () => this.switchMode('sample'));
      this.tabCustom.addEventListener('click', () => this.switchMode('custom'));
    }

    // 3. Load Authentic Sample Transactions
    await this.loadSampleTransactions();

    if (this.sampleSelect) {
      this.sampleSelect.addEventListener('change', (e) => {
        const sampleId = e.target.value;
        this.selectedSample = this.samples.find((s) => s.id === sampleId) || null;
        this.renderSelectedSample();
      });
    }

    if (this.btnRunSample) {
      this.btnRunSample.addEventListener('click', () => {
        this.executeSampleScan();
      });
    }

    // 4. Human Checker Listeners
    if (this.inputElement) {
      this.inputElement.addEventListener('input', (e) => {
        this._detectInputType(e.target.value.trim());
      });

      this.inputElement.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.executeHumanScan();
        }
      });
    }

    const sampleLinks = document.querySelectorAll('.sample-link');
    sampleLinks.forEach((link) => {
      link.addEventListener('click', (e) => {
        const val = e.currentTarget.dataset.sample;
        if (this.inputElement) {
          this.inputElement.value = val;
          this._detectInputType(val);
          this.inputElement.focus();
        }
      });
    });

    if (this.advancedToggle && this.advancedGrid) {
      this.advancedToggle.addEventListener('click', () => {
        const isHidden = this.advancedGrid.style.display === 'none';
        this.advancedGrid.style.display = isHidden ? 'grid' : 'none';
        const arrow = this.advancedToggle.querySelector('.toggle-arrow');
        if (arrow) {
          arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
        }
      });
    }

    if (this.scanBtn) {
      this.scanBtn.addEventListener('click', () => {
        this.executeHumanScan();
      });
    }
  }

  switchMode(mode) {
    if (mode === 'sample') {
      this.tabSample?.classList.add('active');
      this.tabCustom?.classList.remove('active');
      if (this.panelSample) this.panelSample.style.display = 'block';
      if (this.panelCustom) this.panelCustom.style.display = 'none';
    } else {
      this.tabCustom?.classList.add('active');
      this.tabSample?.classList.remove('active');
      if (this.panelCustom) this.panelCustom.style.display = 'block';
      if (this.panelSample) this.panelSample.style.display = 'none';
    }
  }

  async loadSampleTransactions() {
    try {
      this.samples = await api.getSampleTransactions();
      if (!this.sampleSelect) return;

      this.sampleSelect.innerHTML = '';

      if (!this.samples || this.samples.length === 0) {
        this.sampleSelect.innerHTML = '<option value="">No sample transactions available</option>';
        return;
      }

      this.samples.forEach((sample, i) => {
        const opt = document.createElement('option');
        opt.value = sample.id;
        const tag = sample.ground_truth === 1 ? '🚨 FRAUD' : '✅ LEGIT';
        opt.textContent = `[${tag}] ${sample.description} — Amount: $${sample.amount_raw.toFixed(2)}`;
        this.sampleSelect.appendChild(opt);
      });

      // Default select first sample
      this.selectedSample = this.samples[0];
      this.renderSelectedSample();
    } catch (err) {
      console.warn('Could not load sample transactions', err);
    }
  }

  renderSelectedSample() {
    if (!this.selectedSample) return;

    const s = this.selectedSample;
    const titleEl = document.getElementById('sample-card-title');
    const gtEl = document.getElementById('sample-card-gt');
    const amtEl = document.getElementById('sample-card-amount');
    const timeEl = document.getElementById('sample-card-time');

    if (titleEl) titleEl.textContent = s.description;
    if (gtEl) {
      if (s.ground_truth === 1) {
        gtEl.className = 'badge badge-critical';
        gtEl.textContent = 'Ground Truth: FRAUD';
      } else {
        gtEl.className = 'badge badge-safe';
        gtEl.textContent = 'Ground Truth: LEGITIMATE';
      }
    }
    if (amtEl) amtEl.textContent = `$${s.amount_raw.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (timeEl) timeEl.textContent = `${s.time_raw}s (${(s.time_raw / 3600).toFixed(1)}h)`;

    if (this.sampleFeaturesGrid && s.features) {
      this.sampleFeaturesGrid.innerHTML = '';
      for (const [k, v] of Object.entries(s.features)) {
        const item = document.createElement('div');
        item.style.padding = '3px 6px';
        item.style.background = '#F8FAF9';
        item.style.border = '1px solid #E2E8F0';
        item.style.borderRadius = '3px';
        item.innerHTML = `<span style="color: #64716C;">${k}:</span> <b style="color: #17201D;">${typeof v === 'number' ? v.toFixed(3) : v}</b>`;
        this.sampleFeaturesGrid.appendChild(item);
      }
    }
  }

  /**
   * Run Authentic ML Inference on the chosen dataset row (Option A)
   */
  async executeSampleScan() {
    if (this.isScanning || !this.selectedSample) return;

    this.isScanning = true;
    this.btnRunSample.disabled = true;

    const btnText = this.btnRunSample.querySelector('.btn-text');
    await scrambleText(btnText, 'APPLYING STANDARDSCALER TO TIME & AMOUNT...', 400);
    await scrambleText(btnText, 'FEEDING 30-FEATURE VECTOR TO XGBOOST...', 400);
    await scrambleText(btnText, 'COMPUTING CLASS RISK PROBABILITIES...', 400);

    const s = this.selectedSample;
    const payload = {
      query: s.id,
      queryType: 'DATASET_ROW',
      amount: s.amount_raw,
      paymentMethod: 'Credit Card',
      features: s.features
    };

    try {
      const result = await api.analyzeTransaction(payload);

      this.btnRunSample.disabled = false;
      this.isScanning = false;
      btnText.textContent = 'RUN GENUINE ML INFERENCE';

      // Toast feedback
      if (result.prediction === 1) {
        toast.show({
          title: '🚨 XGBoost Flagged Fraud',
          message: `Model identified transaction as FRAUD with ${result.riskScore}% risk probability.`,
          type: 'critical',
          duration: 7000
        });
      } else {
        toast.show({
          title: '✅ XGBoost Verified Legitimate',
          message: `Model verified transaction as LEGITIMATE with ${result.riskScore}% risk score.`,
          type: 'safe',
          duration: 6000
        });
      }

      try {
        sessionStorage.setItem('fraudshield_last_result', JSON.stringify(result));
      } catch (e) {}

      // Navigate to result view
      this.router.navigate('result', { resultData: result });

    } catch (err) {
      this.btnRunSample.disabled = false;
      this.isScanning = false;
      btnText.textContent = 'RUN GENUINE ML INFERENCE';

      toast.show({
        title: 'Inference Error',
        message: err.message || 'Could not execute prediction.',
        type: 'critical',
        duration: 8000
      });
    }
  }

  /**
   * Execute human form submission (Option A diagnostic report)
   */
  async executeHumanScan() {
    if (this.isScanning) return;

    const query = this.inputElement.value.trim();
    if (!query) {
      toast.show({
        title: 'Input Required',
        message: 'Please enter a Transaction ID, Wallet Address, or Customer Email.',
        type: 'info'
      });
      this.inputElement.focus();
      return;
    }

    this.isScanning = true;
    this.scanBtn.disabled = true;

    const btnText = this.scanBtn.querySelector('.btn-text');
    await scrambleText(btnText, 'VALIDATING INPUT PAYLOAD...', 400);
    await scrambleText(btnText, 'CHECKING FEATURE SIGNATURES...', 400);

    const payload = {
      query: query,
      queryType: this.currentQueryType,
      amount: document.getElementById('adv-amount')?.value || '',
      currency: document.getElementById('adv-currency')?.value || 'USD',
      paymentMethod: document.getElementById('adv-payment-method')?.value || 'Credit Card',
      ipAddress: document.getElementById('adv-ip')?.value || '',
      userLocation: document.getElementById('adv-location')?.value || ''
    };

    try {
      const result = await api.analyzeTransaction(payload);

      this.scanBtn.disabled = false;
      this.isScanning = false;
      btnText.textContent = 'TEST BACKEND WITH HUMAN FIELDS';

      if (!result.success) {
        toast.show({
          title: 'Feature Mismatch Notification',
          message: 'The model requires 30 numerical PCA features. View results for full explanation.',
          type: 'info',
          duration: 7000
        });
      }

      try {
        sessionStorage.setItem('fraudshield_last_result', JSON.stringify(result));
      } catch (e) {}

      this.router.navigate('result', { resultData: result });

    } catch (err) {
      this.scanBtn.disabled = false;
      this.isScanning = false;
      btnText.textContent = 'TEST BACKEND WITH HUMAN FIELDS';

      toast.show({
        title: 'Backend Error',
        message: err.message || 'Could not connect to FastAPI server.',
        type: 'critical',
        duration: 8000
      });
    }
  }

  prefill(params = {}) {
    if (params.query && this.inputElement) {
      this.switchMode('custom');
      this.inputElement.value = params.query;
      this._detectInputType(params.query);
    }
    if (params.amount && document.getElementById('adv-amount')) {
      document.getElementById('adv-amount').value = params.amount.replace(/[^0-9.]/g, '');
    }
    if (params.channel && document.getElementById('adv-payment-method')) {
      const select = document.getElementById('adv-payment-method');
      for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].text.toLowerCase().includes(params.channel.toLowerCase())) {
          select.selectedIndex = i;
          break;
        }
      }
    }
  }

  _detectInputType(val) {
    if (!val) {
      if (this.detectPill) this.detectPill.className = 'detect-pill';
      if (this.detectText) this.detectText.textContent = 'Auto-detecting format...';
      if (this.detectIcon) {
        this.detectIcon.innerHTML = `<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/>`;
      }
      this.currentQueryType = 'TX_ID';
      return;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const walletPattern = /^(0x[a-fA-F0-9]{30,42}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$/;

    if (walletPattern.test(val) || val.startsWith('0x')) {
      this.currentQueryType = 'CRYPTO_WALLET';
      if (this.detectPill) this.detectPill.className = 'detect-pill detected';
      if (this.detectText) this.detectText.textContent = 'Detected: Crypto Wallet Address';
      if (this.detectIcon) {
        this.detectIcon.innerHTML = `
          <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" stroke-width="2" fill="none"/>
          <circle cx="16" cy="12" r="2" fill="currentColor"/>
        `;
      }
    } else if (emailPattern.test(val) || val.includes('@')) {
      this.currentQueryType = 'CUSTOMER_EMAIL';
      if (this.detectPill) this.detectPill.className = 'detect-pill detected';
      if (this.detectText) this.detectText.textContent = 'Detected: Customer Email Address';
      if (this.detectIcon) {
        this.detectIcon.innerHTML = `
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2" fill="none"/>
          <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
        `;
      }
    } else {
      this.currentQueryType = 'TX_ID';
      if (this.detectPill) this.detectPill.className = 'detect-pill detected';
      if (this.detectText) this.detectText.textContent = 'Detected: Transaction ID / Hash';
      if (this.detectIcon) {
        this.detectIcon.innerHTML = `
          <line x1="4" y1="9" x2="20" y2="9" stroke="currentColor" stroke-width="2"/>
          <line x1="4" y1="15" x2="20" y2="15" stroke="currentColor" stroke-width="2"/>
          <line x1="10" y1="3" x2="8" y2="21" stroke="currentColor" stroke-width="2"/>
          <line x1="16" y1="3" x2="14" y2="21" stroke="currentColor" stroke-width="2"/>
        `;
      }
    }
  }
}
