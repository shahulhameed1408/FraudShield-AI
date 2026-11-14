/**
 * FraudShield AI - Cyber Toast Notification Manager
 * Handles desktop-style top-right alerts with glowing borders and cyber animations.
 */

class ToastManager {
  constructor() {
    this.container = null;
    this._ensureContainer();
  }

  _ensureContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    this.container = container;
  }

  /**
   * Display a new toast notification
   * @param {Object} options { title, message, type: 'critical' | 'safe' | 'info', duration: 5000 }
   */
  show({ title, message, type = 'info', duration = 5000 }) {
    this._ensureContainer();

    const toast = document.createElement('div');
    toast.className = `cyber-toast ${type} toast-enter`;

    const iconSvg = this._getIcon(type);
    const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    toast.innerHTML = `
      <div class="toast-icon">${iconSvg}</div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
        <div class="toast-time font-mono">${timeString} • AI Watchdog</div>
      </div>
      <button class="toast-close-btn" aria-label="Close Notification">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    `;

    // Handle close button
    const closeBtn = toast.querySelector('.toast-close-btn');
    closeBtn.addEventListener('click', () => this.dismiss(toast));

    this.container.appendChild(toast);

    // Auto dismiss after duration
    if (duration > 0) {
      setTimeout(() => {
        this.dismiss(toast);
      }, duration);
    }

    return toast;
  }

  dismiss(toastElement) {
    if (!toastElement || !toastElement.parentElement) return;
    toastElement.classList.remove('toast-enter');
    toastElement.classList.add('toast-exit');
    setTimeout(() => {
      if (toastElement.parentElement) {
        toastElement.parentElement.removeChild(toastElement);
      }
    }, 300);
  }

  _getIcon(type) {
    if (type === 'critical') {
      return `
        <svg viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      `;
    }
    if (type === 'safe') {
      return `
        <svg viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <polyline points="9 12 11 14 15 10"/>
        </svg>
      `;
    }
    // info / default
    return `
      <svg viewBox="0 0 24 24" fill="none" stroke="#087F5B" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
    `;
  }
}

export const toast = new ToastManager();
