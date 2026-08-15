const APPEARANCE_KEY = 'goreevault-web-appearance';
const MODES = ['system', 'light', 'dark'];

function safeStore(mode) {
  try {
    if (mode === 'system') localStorage.removeItem(APPEARANCE_KEY);
    else localStorage.setItem(APPEARANCE_KEY, mode);
  } catch (_) {
    // Appearance persistence must fail soft and never block vault operation.
  }
}

function setAppearance(mode, announce = false) {
  const value = MODES.includes(mode) ? mode : 'system';
  document.documentElement.dataset.appearance = value;
  safeStore(value);

  const button = document.querySelector('#appearance-toggle');
  if (button) {
    const label = `Appearance: ${value[0].toUpperCase()}${value.slice(1)}`;
    button.setAttribute('aria-label', label);
    button.title = `${label}. Activate to change.`;
  }

  if (announce) {
    const status = document.querySelector('#appearance-status');
    if (status) status.textContent = `Appearance changed to ${value}.`;
  }
}

function currentAppearance() {
  const value = document.documentElement.dataset.appearance;
  return MODES.includes(value) ? value : 'system';
}

function bindAppearance() {
  const button = document.querySelector('#appearance-toggle');
  if (!button) return;

  setAppearance(currentAppearance());
  button.addEventListener('click', () => {
    const current = currentAppearance();
    const next = MODES[(MODES.indexOf(current) + 1) % MODES.length];
    setAppearance(next, true);
  });
}

function bindSkipTarget() {
  const main = document.querySelector('#main');
  if (!main) return;
  main.addEventListener('focus', () => main.scrollIntoView({ block: 'start' }), { once: true });
}

bindAppearance();
bindSkipTarget();
