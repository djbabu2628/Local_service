/* ============================================================
   theme.js — LSES Theme Switcher
   8 Beautiful Palettes with localStorage persistence
============================================================ */

const THEMES = [
  { id:'noir',     name:'Noir',     cls:'sw-noir'     },
  { id:'ivory',    name:'Ivory',    cls:'sw-ivory'    },
  { id:'ocean',    name:'Ocean',    cls:'sw-ocean'    },
  { id:'ember',    name:'Ember',    cls:'sw-ember'    },
  { id:'forest',   name:'Forest',   cls:'sw-forest'   },
  { id:'rose',     name:'Rose',     cls:'sw-rose'     },
  { id:'sapphire', name:'Sapphire', cls:'sw-sapphire' },
  { id:'volt',     name:'Volt',     cls:'sw-volt'     },
];

function applyTheme(id) {
  document.documentElement.setAttribute('data-theme', id);
  localStorage.setItem('lses-theme', id);
  // Mark active swatch
  document.querySelectorAll('.theme-swatch').forEach(el => {
    el.classList.toggle('active', el.dataset.theme === id);
  });
}

function toggleThemePanel() {
  const panel = document.getElementById('theme-panel');
  if (!panel) return;
  panel.classList.toggle('open');
}

// Close panel when clicking outside
document.addEventListener('click', function(e) {
  const panel = document.getElementById('theme-panel');
  const btn   = document.getElementById('theme-trigger');
  if (!panel || !btn) return;
  if (!panel.contains(e.target) && !btn.contains(e.target)) {
    panel.classList.remove('open');
  }
});

// Build the panel HTML and inject it
function buildThemeUI() {
  // Trigger button
  const trigger = document.createElement('button');
  trigger.className = 'theme-trigger';
  trigger.id = 'theme-trigger';
  trigger.setAttribute('title', 'Change Theme');
  trigger.innerHTML = '🎨';
  trigger.onclick = toggleThemePanel;
  document.body.appendChild(trigger);

  // Panel
  const panel = document.createElement('div');
  panel.className = 'theme-panel';
  panel.id = 'theme-panel';

  const title = document.createElement('div');
  title.className = 'theme-panel-title';
  title.textContent = 'Choose Theme';
  panel.appendChild(title);

  const grid = document.createElement('div');
  grid.className = 'theme-grid';

  const current = localStorage.getItem('lses-theme') || 'noir';

  THEMES.forEach(t => {
    const sw = document.createElement('div');
    sw.className = 'theme-swatch' + (t.id === current ? ' active' : '');
    sw.dataset.theme = t.id;
    sw.onclick = () => { applyTheme(t.id); };
    sw.innerHTML = `
      <div class="swatch-dot ${t.cls}"></div>
      <span class="swatch-name">${t.name}</span>
    `;
    grid.appendChild(sw);
  });

  panel.appendChild(grid);
  document.body.appendChild(panel);
}

// Init on load
window.addEventListener('DOMContentLoaded', function() {
  buildThemeUI();
  const saved = localStorage.getItem('lses-theme') || 'noir';
  document.documentElement.setAttribute('data-theme', saved);
});
