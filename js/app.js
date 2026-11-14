/**
 * FraudShield AI - Main Application Entrypoint
 */

import { SidebarManager } from './sidebar.js';
import { Router } from './router.js';
import { DashboardView } from './views/dashboardView.js';
import { CheckerView } from './views/checkerView.js';
import { ResultView } from './views/resultView.js';
import { AlertsView } from './views/alertsView.js';
import { SettingsView } from './views/settingsView.js';
import { toast } from './toast.js';
import { api } from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Layout & Sidebar
  const sidebar = new SidebarManager();

  // 2. Initialize Router
  const router = new Router();

  // 3. Initialize Views
  const dashboardView = new DashboardView(router);
  const checkerView = new CheckerView(router);
  const resultView = new ResultView(router);
  const alertsView = new AlertsView(router);
  const settingsView = new SettingsView(router);

  // Register views with router
  router.register('dashboard', dashboardView);
  router.register('scanner', checkerView);
  router.register('result', resultView);
  router.register('alerts', alertsView);
  router.register('settings', settingsView);

  // Initialize individual views
  await dashboardView.init();
  await checkerView.init();
  resultView.init();
  await alertsView.init();
  settingsView.init();

  // 4. Attach Nav Click Listeners
  const navLinks = document.querySelectorAll('.nav-item');
  navLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const route = e.currentTarget.dataset.route;
      if (route) {
        router.navigate(route);
      }
    });
  });

  // 5. Global Search Bar & Keyboard Shortcut (Ctrl+K)
  const topbarSearch = document.getElementById('topbar-global-search');
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (topbarSearch) {
        topbarSearch.focus();
        topbarSearch.select();
      }
    }
  });

  if (topbarSearch) {
    topbarSearch.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const query = topbarSearch.value.trim();
        if (query) {
          router.navigate('scanner', { query });
          topbarSearch.value = '';
          topbarSearch.blur();
        }
      }
    });
  }

  // 6. Navigate to initial route from URL Hash
  const initialHash = window.location.hash.replace('#', '') || 'dashboard';
  router.navigate(initialHash, null, false);

  // 7. Check backend health & update topbar indicator
  try {
    const health = await api.checkHealth();
    const statusText = document.getElementById('topbar-engine-text');
    const statusDot = document.querySelector('.status-indicator-dot');
    if (health.model_loaded && health.preprocessing_ready) {
      if (statusText) statusText.textContent = 'AI Engine: XGBoost Online';
      if (statusDot) statusDot.className = 'status-indicator-dot pulse-dot-emerald';
      setTimeout(() => {
        toast.show({
          title: 'XGBoost Engine Online',
          message: 'Trained model and preprocessing scalers loaded. Ready for 30-feature inference.',
          type: 'safe',
          duration: 4000
        });
      }, 800);
    } else {
      if (statusText) statusText.textContent = 'AI Engine: Offline / Standby';
      if (statusDot) {
        statusDot.className = 'status-indicator-dot';
        statusDot.style.background = 'var(--status-warning)';
      }
    }
  } catch (e) {
    console.warn('Initial health check notice', e);
  }
});
