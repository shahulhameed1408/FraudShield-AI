/**
 * FraudShield AI - Interactive SVG Area/Line Chart Component
 * Professional Light Theme Edition (Deep Emerald & Fraud Red)
 */

export class AttackChart {
  constructor(containerElement) {
    this.container = containerElement;
    this.width = 900;
    this.height = 280;
    this.padding = { top: 20, right: 30, bottom: 40, left: 50 };
    this.tooltip = null;
    this._init();
  }

  _init() {
    this.container.innerHTML = `
      <div class="svg-chart-wrapper">
        <svg class="svg-chart" viewBox="0 0 ${this.width} ${this.height}" preserveAspectRatio="none">
          <defs>
            <linearGradient id="emeraldGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#087F5B" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="#087F5B" stop-opacity="0.0"/>
            </linearGradient>
            <linearGradient id="crimsonGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#DC2626" stop-opacity="0.2"/>
              <stop offset="100%" stop-color="#DC2626" stop-opacity="0.0"/>
            </linearGradient>
          </defs>

          <!-- Grid Lines -->
          <g id="chart-grid"></g>

          <!-- Area Paths -->
          <path id="chart-area-total" class="chart-area-total" />
          <path id="chart-area-fraud" class="chart-area-fraud" />

          <!-- Line Paths -->
          <path id="chart-line-total" class="chart-line-total" />
          <path id="chart-line-fraud" class="chart-line-fraud" />

          <!-- Interactive Points -->
          <g id="chart-points"></g>

          <!-- Axes Labels -->
          <g id="chart-labels"></g>
        </svg>

        <div id="chart-tooltip" class="chart-tooltip"></div>
      </div>
    `;

    this.svg = this.container.querySelector('.svg-chart');
    this.gridG = this.container.querySelector('#chart-grid');
    this.areaTotal = this.container.querySelector('#chart-area-total');
    this.areaFraud = this.container.querySelector('#chart-area-fraud');
    this.lineTotal = this.container.querySelector('#chart-line-total');
    this.lineFraud = this.container.querySelector('#chart-line-fraud');
    this.pointsG = this.container.querySelector('#chart-points');
    this.labelsG = this.container.querySelector('#chart-labels');
    this.tooltip = this.container.querySelector('#chart-tooltip');
  }

  /**
   * Render chart with data
   * @param {Object} data { labels: [], totalScans: [], fraudAttempts: [] }
   */
  render(data) {
    if (!data || !data.labels) return;
    const { labels, totalScans, fraudAttempts } = data;

    const plotW = this.width - this.padding.left - this.padding.right;
    const plotH = this.height - this.padding.top - this.padding.bottom;

    const maxTotal = Math.max(...totalScans) * 1.15 || 100;
    const maxFraud = Math.max(...fraudAttempts) * 1.3 || 10;

    // Helper coordinates
    const getX = (index) => this.padding.left + (index / (labels.length - 1)) * plotW;
    const getYTotal = (val) => this.padding.top + plotH - (val / maxTotal) * plotH;
    const getYFraud = (val) => this.padding.top + plotH - (val / maxFraud) * (plotH * 0.75);

    // 1. Draw Grid Lines (Horizontal)
    let gridHtml = '';
    const gridSteps = 4;
    for (let i = 0; i <= gridSteps; i++) {
      const y = this.padding.top + (i / gridSteps) * plotH;
      gridHtml += `<line x1="${this.padding.left}" y1="${y}" x2="${this.width - this.padding.right}" y2="${y}" class="chart-grid-line" />`;
    }
    this.gridG.innerHTML = gridHtml;

    // 2. Generate Smooth Paths
    const totalPoints = totalScans.map((val, i) => ({ x: getX(i), y: getYTotal(val), val }));
    const fraudPoints = fraudAttempts.map((val, i) => ({ x: getX(i), y: getYFraud(val), val }));

    const totalLinePath = this._buildSmoothPath(totalPoints);
    const fraudLinePath = this._buildSmoothPath(fraudPoints);

    this.lineTotal.setAttribute('d', totalLinePath);
    this.lineFraud.setAttribute('d', fraudLinePath);

    // Area Paths
    const baselineY = this.padding.top + plotH;
    const totalAreaPath = `${totalLinePath} L ${totalPoints[totalPoints.length - 1].x} ${baselineY} L ${totalPoints[0].x} ${baselineY} Z`;

    this.areaTotal.setAttribute('d', totalAreaPath);
    this.areaFraud.setAttribute('d', `${fraudLinePath} L ${fraudPoints[fraudPoints.length - 1].x} ${baselineY} L ${fraudPoints[0].x} ${baselineY} Z`);

    // 3. X Labels
    let labelsHtml = '';
    labels.forEach((lbl, i) => {
      labelsHtml += `
        <text x="${getX(i)}" y="${this.height - 12}" text-anchor="middle" class="chart-axis-label">${lbl}</text>
      `;
    });
    this.labelsG.innerHTML = labelsHtml;

    // 4. Interactive Points
    let pointsHtml = '';
    fraudPoints.forEach((pt, i) => {
      pointsHtml += `
        <circle 
          cx="${pt.x}" cy="${pt.y}" r="4.5" 
          fill="#DC2626" stroke="#FFFFFF" stroke-width="2"
          class="chart-point"
          data-index="${i}"
          style="cursor: pointer; transition: transform 0.2s;"
        />
      `;
    });
    this.pointsG.innerHTML = pointsHtml;

    // 5. Attach Hover Listeners
    const circles = this.pointsG.querySelectorAll('.chart-point');
    circles.forEach((circle) => {
      circle.addEventListener('mouseenter', (e) => {
        const idx = Number(e.target.dataset.index);
        const pt = fraudPoints[idx];
        const label = labels[idx];
        const fraudVal = fraudAttempts[idx];
        const totalVal = totalScans[idx];

        e.target.setAttribute('r', '7');
        e.target.style.filter = 'drop-shadow(0 2px 4px rgba(220, 38, 38, 0.4))';

        this.tooltip.style.display = 'block';
        this.tooltip.style.left = `${(pt.x / this.width) * 100}%`;
        this.tooltip.style.top = `${(pt.y / this.height) * 100}%`;
        this.tooltip.innerHTML = `
          <div style="font-weight: 600; color: #FFFFFF; margin-bottom: 4px; font-family: var(--font-heading);">${label}</div>
          <div style="color: #20C997;">Total Scans: <b>${totalVal.toLocaleString()}</b></div>
          <div style="color: #F87171;">Fraud Intercepted: <b>${fraudVal.toLocaleString()}</b></div>
        `;
      });

      circle.addEventListener('mouseleave', (e) => {
        e.target.setAttribute('r', '4.5');
        e.target.style.filter = 'none';
        this.tooltip.style.display = 'none';
      });
    });
  }

  /**
   * Helper to construct cubic bezier smooth curve
   */
  _buildSmoothPath(points) {
    if (points.length === 0) return '';
    if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

    let path = `M ${points[0].x} ${points[0].y}`;

    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? 0 : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2 < points.length ? i + 2 : i + 1];

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;

      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }

    return path;
  }
}
