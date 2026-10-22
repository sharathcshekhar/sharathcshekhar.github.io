/**
 * Main Interactive Features for Sharath Chandrashekhara Portfolio
 * sch-home vanilla JS
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initMobileMenu();
  initBibTeXInteractions();
  initPubFilters();
});

/**
 * Dark / Light Mode Switcher with localStorage persistence
 */
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    showToast(`Switched to ${newTheme} mode`);
  });
}

/**
 * Mobile Navigation Drawer Toggle
 */
function initMobileMenu() {
  const menuBtn = document.getElementById('mobile-menu-toggle');
  const navList = document.querySelector('.nav-list');
  if (!menuBtn || !navList) return;

  menuBtn.addEventListener('click', () => {
    navList.classList.toggle('is-open');
    menuBtn.classList.toggle('is-active');
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!menuBtn.contains(e.target) && !navList.contains(e.target)) {
      navList.classList.remove('is-open');
      menuBtn.classList.remove('is-active');
    }
  });
}

/**
 * BibTeX Copy-to-Clipboard & Inline Preview Toggler
 */
function initBibTeXInteractions() {
  // Copy BibTeX
  document.addEventListener('click', (e) => {
    const copyBtn = e.target.closest('.copy-bibtex-btn');
    if (!copyBtn) return;

    const bibtex = copyBtn.getAttribute('data-bibtex');
    if (!bibtex) return;

    // Decode HTML entities
    const parser = new DOMParser();
    const decoded = parser.parseFromString(bibtex, 'text/html').body.textContent;

    navigator.clipboard.writeText(decoded).then(() => {
      showToast('BibTeX citation copied to clipboard!');
    }).catch(() => {
      // Fallback
      const textarea = document.createElement('textarea');
      textarea.value = decoded;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      showToast('BibTeX citation copied to clipboard!');
    });
  });

  // Toggle View BibTeX
  document.addEventListener('click', (e) => {
    const viewBtn = e.target.closest('.toggle-bibtex-view');
    if (!viewBtn) return;

    const targetId = viewBtn.getAttribute('data-target');
    const targetEl = document.getElementById(targetId);
    if (targetEl) {
      targetEl.classList.toggle('hidden');
    }
  });
}

/**
 * Publication Filtering on Research Page
 */
function initPubFilters() {
  const filterContainer = document.getElementById('pub-filters');
  const pubCards = document.querySelectorAll('.pub-card');
  if (!filterContainer || pubCards.length === 0) return;

  filterContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;

    filterContainer.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const filter = btn.getAttribute('data-filter');

    pubCards.forEach(card => {
      if (filter === 'all') {
        card.classList.remove('hidden');
      } else if (filter === 'Patent') {
        const hasPatentBadge = card.querySelector('.badge')?.textContent.includes('Patent');
        card.classList.toggle('hidden', !hasPatentBadge);
      } else {
        const id = card.id || '';
        const title = card.querySelector('.pub-title')?.textContent || '';
        const match = id.toLowerCase().includes(filter.toLowerCase()) || title.toLowerCase().includes(filter.toLowerCase());
        card.classList.toggle('hidden', !match);
      }
    });
  });
}

/**
 * Reusable Toast Notification Notification Helper
 */
function showToast(message, duration = 2500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }, duration);
}
