/**
 * FraudShield AI - Alerts Log & History View Controller (Page 4 / History)
 * Connects directly to SQLite persistent history via FastAPI /history endpoints.
 */

import { api } from '../api.js';
import { toast } from '../toast.js';

export class AlertsView {
  constructor(router) {
    this.router = router;
    this.alerts = [];
    this.currentFilter = 'ALL';
    this.searchInput = null;
    this.tableBody = null;
    this.isLoading = false;
  }

  async init() {
    this.tableBody = document.getElementById('alerts-table-body');
    this.searchInput = document.getElementById('alerts-search-input');

    // Attach Filter Buttons
    const filterBtns = document.querySelectorAll('.alert-filter-btn');
    filterBtns.forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        filterBtns.forEach((b) => b.classList.remove('active'));
        e.target.classList.add('active');
        this.currentFilter = e.target.dataset.filter;
        await this.loadAlerts();
      });
    });

    // Attach Search Input Listener
    if (this.searchInput) {
      let debounceTimeout = null;
      this.searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
          this.loadAlerts();
        }, 300);
      });
    }

    // Load initial alerts from backend
    await this.loadAlerts();
  }

  async loadAlerts() {
    if (!this.tableBody) return;

    this.isLoading = true;
    this.tableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 36px; color: var(--text-muted);">
          <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
            <span class="status-indicator-dot pulse-dot-emerald" style="width: 8px; height: 8px;"></span>
            Querying persistent history from SQLite...
          </div>
        </td>
      </tr>
    `;

    try {
      const searchVal = this.searchInput?.value.trim() || undefined;
      const history = await api.getHistory({
        status: this.currentFilter,
        search: searchVal
      });

      this.alerts = history || [];
      this._renderTable(this.alerts);
    } catch (err) {
      console.warn('Failed to fetch history from backend', err);
      this.tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 36px; color: var(--status-danger);">
            Could not retrieve history from backend: ${err.message}. Ensure FastAPI is running.
          </td>
        </tr>
      `;
    } finally {
      this.isLoading = false;
    }
  }

  _renderTable(items) {
    if (!this.tableBody) return;
    this.tableBody.innerHTML = '';

    if (!items || items.length === 0) {
      this.tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 36px; color: var(--text-muted);">
            No analysis records found matching current query. Run a scan in the Transaction Scanner to see records here.
          </td>
        </tr>
      `;
      return;
    }

    items.forEach((item) => {
      const tr = document.createElement('tr');
      if (item.verdict === 'CRITICAL') tr.className = 'row-critical';

      let badgeHtml = '';
      if (item.verdict === 'SAFE') {
        badgeHtml = `<span class="badge badge-safe"><span class="badge-dot"></span>Safe (${item.riskScore}%)</span>`;
      } else if (item.verdict === 'REVIEW') {
        badgeHtml = `<span class="badge badge-review"><span class="badge-dot"></span>Review (${item.riskScore}%)</span>`;
      } else {
        badgeHtml = `<span class="badge badge-critical pulse-crimson"><span class="badge-dot"></span>Critical (${item.riskScore}%)</span>`;
      }

      const formattedTime = item.timestamp ? (
        item.timestamp.includes('T') ? item.timestamp.replace('T', ' ').split('.')[0] : item.timestamp
      ) : 'Recent';

      tr.innerHTML = `
        <td><span class="font-mono" style="color: var(--primary); font-weight: 600;">${item.transactionId}</span></td>
        <td><span style="color: var(--text-muted); font-size: 11.5px;">${formattedTime}</span></td>
        <td><span class="font-mono">${item.entity || item.transactionId}</span></td>
        <td><span class="badge" style="background: var(--bg-subtle); color: var(--text-secondary);">${item.channel || 'Credit Card'}</span></td>
        <td><span class="font-mono" style="font-weight: 600;">${item.amount || '$0.00'}</span></td>
        <td>${badgeHtml}</td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="btn btn-secondary btn-sm inspect-alert-btn" data-id="${item.id}" title="Inspect Analysis Result">
            Inspect
          </button>
          <button class="btn btn-sm delete-alert-btn" data-id="${item.id}" title="Delete Record" style="background: transparent; color: var(--text-muted); border: 1px solid var(--border-subtle); padding: 4px 8px; margin-left: 4px;">
            &times;
          </button>
        </td>
      `;

      // Action: Inspect
      const inspectBtn = tr.querySelector('.inspect-alert-btn');
      inspectBtn.addEventListener('click', async () => {
        try {
          const fullRecord = await api.getHistoryById(item.id);
          this.router.navigate('result', {
            resultData: {
              success: true,
              transactionId: fullRecord.transactionId,
              queriedEntity: fullRecord.entity,
              channel: fullRecord.channel,
              amount: fullRecord.amount,
              rawAmount: fullRecord.rawAmount,
              prediction: fullRecord.prediction,
              fraud_status: fullRecord.fraudStatus,
              riskScore: fullRecord.riskScore,
              risk_score: fullRecord.riskScore,
              verdict: fullRecord.verdict,
              message: fullRecord.message,
              is_mock: fullRecord.isMock,
              ipLocation: fullRecord.ipAddress,
              userLocation: fullRecord.userLocation
            }
          });
        } catch (e) {
          toast.show({
            title: 'Inspection Error',
            message: 'Could not load record details.',
            type: 'critical'
          });
        }
      });

      // Action: Delete
      const deleteBtn = tr.querySelector('.delete-alert-btn');
      deleteBtn.addEventListener('click', async () => {
        try {
          await api.deleteHistory(item.id);
          toast.show({
            title: 'Record Deleted',
            message: `Removed ${item.transactionId} from database.`,
            type: 'safe'
          });
          await this.loadAlerts();
        } catch (err) {
          toast.show({
            title: 'Deletion Failed',
            message: err.message || 'Could not delete record.',
            type: 'critical'
          });
        }
      });

      this.tableBody.appendChild(tr);
    });
  }
}
