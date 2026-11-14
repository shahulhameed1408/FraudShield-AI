/**
 * FraudShield AI - Persistent Sidebar Manager
 * Controls expand/collapse states, mobile slide-over drawer, and persistence.
 */

export class SidebarManager {
  constructor() {
    this.sidebar = document.getElementById('sidebar');
    this.toggleBtn = document.getElementById('sidebar-toggle-btn');
    this.mobileMenuBtn = document.getElementById('mobile-menu-btn');
    this.overlay = document.getElementById('sidebar-overlay');
    this._init();
  }

  _init() {
    if (!this.sidebar) return;

    // Load saved collapsed state for desktop
    const isCollapsed = localStorage.getItem('fraudshield_sidebar_collapsed') === 'true';
    if (isCollapsed && window.innerWidth > 820) {
      this.sidebar.classList.add('collapsed');
    }

    // Desktop Collapse Toggle Button
    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => {
        this.sidebar.classList.toggle('collapsed');
        const state = this.sidebar.classList.contains('collapsed');
        localStorage.setItem('fraudshield_sidebar_collapsed', state);
      });
    }

    // Mobile Hamburger Menu Button
    if (this.mobileMenuBtn) {
      this.mobileMenuBtn.addEventListener('click', () => {
        this.openMobile();
      });
    }

    // Mobile Drawer Overlay
    if (this.overlay) {
      this.overlay.addEventListener('click', () => {
        this.closeMobile();
      });
    }

    // Auto close mobile drawer on nav item click
    const navItems = this.sidebar.querySelectorAll('.nav-item');
    navItems.forEach((item) => {
      item.addEventListener('click', () => {
        if (window.innerWidth <= 820) {
          this.closeMobile();
        }
      });
    });
  }

  openMobile() {
    if (this.sidebar) this.sidebar.classList.add('mobile-open');
    if (this.overlay) this.overlay.classList.add('active');
  }

  closeMobile() {
    if (this.sidebar) this.sidebar.classList.remove('mobile-open');
    if (this.overlay) this.overlay.classList.remove('active');
  }
}
