/**
 * FraudShield AI - Analytics Dashboard View Controller (Page 1)
 */

import { api } from '../api.js';
import { AttackChart } from '../components/chart.js';

export class DashboardView {
  constructor(router) {
    this.router = router;
    this.chart = null;
    this.currentTimeframe = '24h';
    this.liveFeedInterval = null;
  }

  async init() {
    this._initChart();
    await this.loadKPIs();
    await this.loadChartData('24h');
    await this.loadLiveFeed();
    this._startLiveSimulation();
  }

  _initChart() {
    const chartContainer = document.getElementById('dashboard-attack-chart-container');
    if (chartContainer) {
      this.chart = new AttackChart(chartContainer);
    }

    // Attach timeframe buttons
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');
    timeframeBtns.forEach((btn) => {
      btn.addEventListener('click', async (e) => {
        timeframeBtns.forEach((b) => b.classList.remove('active'));
        e.target.classList.add('active');
        const tf = e.target.dataset.timeframe;
        this.currentTimeframe = tf;
        await this.loadChartData(tf);
      });
    });
  }

  async loadKPIs() {
    const kpis = await api.getDashboardKPIs();

    const elTotal = document.getElementById('kpi-total-scanned');
    const elBlocked = document.getElementById('kpi-blocked-attempts');
    const elRisk = document.getElementById('kpi-risk-index');
    const elEfficiency = document.getElementById('kpi-ai-efficiency');

    if (elTotal) elTotal.textContent = kpis.totalScanned.toLocaleString();
    if (elBlocked) elBlocked.textContent = kpis.blockedAttempts.toLocaleString();
    if (elRisk) elRisk.textContent = `${kpis.currentRiskIndex}/100`;
    if (elEfficiency) elEfficiency.textContent = kpis.aiEfficiency;
  }

  async loadChartData(timeframe) {
    if (!this.chart) return;
    const data = await api.getAttackChartData(timeframe);
    this.chart.render(data);
  }

  async loadLiveFeed() {
    const tableBody = document.getElementById('live-feed-table-body');
    if (!tableBody) return;

    const feed = await api.getLiveFeed();
    tableBody.innerHTML = '';

    feed.forEach((item) => {
      const row = this._createFeedRow(item);
      tableBody.appendChild(row);
    });
  }

  _createFeedRow(item) {
    const tr = document.createElement('tr');
    if (item.status === 'CRITICAL') {
      tr.className = 'row-critical';
    }

    let badgeHtml = '';
    if (item.status === 'SAFE') {
      badgeHtml = `<span class="badge badge-safe"><span class="badge-dot"></span>Safe</span>`;
    } else if (item.status === 'REVIEW') {
      badgeHtml = `<span class="badge badge-review"><span class="badge-dot"></span>Review</span>`;
    } else {
      badgeHtml = `<span class="badge badge-critical pulse-crimson"><span class="badge-dot"></span>Critical</span>`;
    }

    tr.innerHTML = `
      <td><span class="font-mono" style="color: var(--primary); font-weight: 600;">${item.id}</span></td>
      <td><span style="color: var(--text-muted); font-size: 11.5px;">${item.time}</span></td>
      <td><span class="font-mono" style="font-weight: 600;">${item.entity}</span></td>
      <td><span class="badge" style="background: var(--bg-subtle); color: var(--text-secondary);">${item.channel}</span></td>
      <td><span class="font-mono" style="font-weight: 600;">${item.amount}</span></td>
      <td>${badgeHtml}</td>
      <td style="text-align: right;">
        <button class="btn btn-secondary btn-sm inspect-btn" data-id="${item.id}" data-entity="${item.entity}" data-channel="${item.channel}" data-amount="${item.amount}">
          Inspect
        </button>
      </td>
    `;

    // Action button
    const inspectBtn = tr.querySelector('.inspect-btn');
    inspectBtn.addEventListener('click', (e) => {
      const id = e.currentTarget.dataset.id;
      const entity = e.currentTarget.dataset.entity;
      const channel = e.currentTarget.dataset.channel;
      const amount = e.currentTarget.dataset.amount;

      // Navigate to Checker with prefilled query
      this.router.navigate('scanner', { query: entity || id, channel, amount });
    });

    return tr;
  }

  _startLiveSimulation() {
    if (this.liveFeedInterval) clearInterval(this.liveFeedInterval);

    // Periodically insert live transaction events to demonstrate active watchdog
    this.liveFeedInterval = setInterval(() => {
      const tableBody = document.getElementById('live-feed-table-body');
      if (!tableBody || !document.getElementById('view-dashboard').classList.contains('active')) return;

      const randomTypes = [
        { entity: `TXN-${Math.floor(100000 + Math.random() * 900000)}`, channel: 'Card Payment', amount: `$${(Math.random() * 200 + 20).toFixed(2)}`, status: 'SAFE' },
        { entity: `0x${Math.random().toString(16).substring(2, 6)}...${Math.random().toString(16).substring(2, 6)}`, channel: 'Web3 Transfer', amount: `$${(Math.random() * 3000 + 100).toFixed(2)}`, status: 'REVIEW' },
        { entity: `suspicious_${Math.floor(Math.random() * 1000)}@tempmail.org`, channel: 'Instant Wire', amount: `$${(Math.random() * 8000 + 2000).toFixed(2)}`, status: 'CRITICAL' }
      ];

      const chosen = randomTypes[Math.floor(Math.random() * randomTypes.length)];
      const newTx = {
        id: `TXN-${Math.floor(100000 + Math.random() * 900000)}`,
        time: 'Just now',
        entity: chosen.entity,
        channel: chosen.channel,
        amount: chosen.amount,
        status: chosen.status
      };

      const newRow = this._createFeedRow(newTx);
      newRow.style.opacity = '0';
      newRow.style.transform = 'translateY(-10px)';
      newRow.style.transition = 'all 0.4s ease';

      tableBody.insertBefore(newRow, tableBody.firstChild);

      requestAnimationFrame(() => {
        newRow.style.opacity = '1';
        newRow.style.transform = 'translateY(0)';
      });

      // Keep maximum 8 items in the feed
      if (tableBody.children.length > 8) {
        tableBody.removeChild(tableBody.lastChild);
      }
    }, 18000);
  }
}
