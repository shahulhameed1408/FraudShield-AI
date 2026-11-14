/**
 * FraudShield AI - Dynamic Circular Risk Score Gauge Dial (0 - 100%)
 * Professional Light Theme Edition with Precise Status Colors
 */

export class RiskGauge {
  /**
   * @param {HTMLElement} containerElement The element to render the gauge into
   * @param {number} size Radius / size of the gauge in px (default 200)
   */
  constructor(containerElement, size = 200) {
    this.container = containerElement;
    this.size = size;
    this.radius = 80;
    this.strokeWidth = 14;
    this.circumference = 2 * Math.PI * this.radius;
    this._init();
  }

  _init() {
    this.container.innerHTML = `
      <div class="gauge-svg-container" style="width: ${this.size}px; height: ${this.size}px;">
        <svg viewBox="0 0 200 200" style="width: 100%; height: 100%; transform: rotate(-90deg);">
          <!-- Background Track -->
          <circle
            cx="100" cy="100" r="${this.radius}"
            fill="transparent"
            stroke="#E2E8E5"
            stroke-width="${this.strokeWidth}"
          />
          <!-- Decorative Tick Marks Circle -->
          <circle
            cx="100" cy="100" r="${this.radius + 12}"
            fill="transparent"
            stroke="#CBD5D0"
            stroke-width="1.5"
            stroke-dasharray="2 8"
          />
          <!-- Dynamic Animated Progress Stroke -->
          <circle
            id="gauge-progress-circle"
            cx="100" cy="100" r="${this.radius}"
            fill="transparent"
            stroke="#16A34A"
            stroke-width="${this.strokeWidth}"
            stroke-dasharray="${this.circumference}"
            stroke-dashoffset="${this.circumference}"
            stroke-linecap="round"
            style="transition: stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1), stroke 0.3s ease;"
          />
        </svg>
        <div class="gauge-center-text">
          <span id="gauge-score-num" class="gauge-score-value font-mono">0%</span>
          <span id="gauge-score-status" class="gauge-score-label">CALCULATING</span>
        </div>
      </div>
    `;

    this.progressCircle = this.container.querySelector('#gauge-progress-circle');
    this.scoreNum = this.container.querySelector('#gauge-score-num');
    this.scoreStatus = this.container.querySelector('#gauge-score-status');
  }

  /**
   * Update the gauge to a given score (0-100)
   * @param {number} score Value between 0 and 100
   */
  setScore(score) {
    const clampedScore = Math.max(0, Math.min(100, Math.round(score)));
    const offset = this.circumference - (clampedScore / 100) * this.circumference;

    // Status Color Rules:
    // SAFE: #16A34A (< 35)
    // WARNING/MEDIUM RISK: #D97706 (35-74)
    // FRAUD/HIGH RISK: #DC2626 (>= 75)
    let color = '#16A34A';
    let statusText = 'SAFE THREAT';

    if (clampedScore >= 75) {
      color = '#DC2626';
      statusText = 'HIGH RISK';
    } else if (clampedScore >= 35) {
      color = '#D97706';
      statusText = 'ELEVATED RISK';
    }

    this.progressCircle.style.stroke = color;
    this.progressCircle.style.strokeDashoffset = offset;

    // Number counting animation
    this._animateCount(clampedScore);
    this.scoreStatus.textContent = statusText;
    this.scoreStatus.style.color = color;
  }

  _animateCount(target) {
    let current = 0;
    const duration = 1000;
    const steps = 25;
    const increment = target / steps;
    const stepTime = duration / steps;

    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        clearInterval(timer);
        this.scoreNum.textContent = `${target}%`;
      } else {
        this.scoreNum.textContent = `${Math.round(current)}%`;
      }
    }, stepTime);
  }
}
