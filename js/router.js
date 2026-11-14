/**
 * FraudShield AI - View Router
 * Seamless single-workspace routing handling view transitions, breadcrumbs, and deep-linking.
 */

export class Router {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    this.breadcrumbTitle = document.getElementById('breadcrumb-current');
    this.navItems = document.querySelectorAll('.nav-item');
    this.views = document.querySelectorAll('.view-section');

    this._initHashListener();
  }

  register(routeId, controller) {
    this.routes[routeId] = controller;
  }

  _initHashListener() {
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '') || 'dashboard';
      this.navigate(hash, null, false);
    });
  }

  /**
   * Navigate to a view
   * @param {string} routeId Identifier (dashboard, scanner, result, alerts, settings)
   * @param {any} data Optional data passed to the target view
   * @param {boolean} updateHash Whether to push state to URL hash
   */
  navigate(routeId, data = null, updateHash = true) {
    const targetRoute = this.routes[routeId] ? routeId : 'dashboard';
    this.currentRoute = targetRoute;

    if (updateHash && window.location.hash !== `#${targetRoute}`) {
      window.location.hash = targetRoute;
    }

    // 1. Hide all views, show active view
    this.views.forEach((v) => {
      v.classList.remove('active', 'view-transition');
    });

    const activeView = document.getElementById(`view-${targetRoute}`);
    if (activeView) {
      activeView.classList.add('active', 'view-transition');
    }

    // 2. Update Sidebar Active State
    this.navItems.forEach((item) => {
      const route = item.dataset.route;
      if (route === targetRoute) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // 3. Update Breadcrumb Text
    const routeTitles = {
      dashboard: 'Analytics Dashboard',
      scanner: 'Transaction Scan (Deep Scan Tool)',
      result: 'Deep Scan Result View',
      alerts: 'Alerts Log & History',
      settings: 'System Settings'
    };

    if (this.breadcrumbTitle) {
      this.breadcrumbTitle.textContent = routeTitles[targetRoute] || 'Dashboard';
    }

    // 4. Trigger target controller lifecycle
    const controller = this.routes[targetRoute];
    if (controller) {
      if (targetRoute === 'result' && data && data.resultData) {
        controller.display(data.resultData);
      } else if (targetRoute === 'scanner' && data) {
        controller.prefill(data);
      }
    }

    // Scroll to top of view
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}
