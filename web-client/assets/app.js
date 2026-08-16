import { runtimeConfig, resolveServerOrigin } from './runtime-config.js';
import { getSessionSnapshot, subscribeSession } from './session-state.js';
import { cryptoBoundary } from './crypto-boundary.js';
import { requestPreloginMetadata, normalizeAccountIdentifier } from './auth-protocol.js';
import { requestServerConfig } from './server-config.js';
import {
  acceptPrelogin,
  beginPrelogin,
  rejectAuthentication,
  subscribeAuth,
} from './auth-state.js';

const APPEARANCE_KEY = 'goreevault-web-appearance';
const MODES = ['system', 'light', 'dark'];
const PREALPHA_DISABLED_ROUTES = new Set(['favorites', 'organizations', 'send']);
const TOAST_DURATION_MS = 5000;
let verifiedServerConfig = null;
let toastTimer = null;

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

function routeFromHash() {
  return window.location.hash.replace(/^#/, '').trim().toLowerCase();
}

function hideToast() {
  const toast = document.querySelector('#app-toast');
  if (!(toast instanceof HTMLElement)) return;
  toast.hidden = true;
  if (toastTimer !== null) {
    window.clearTimeout(toastTimer);
    toastTimer = null;
  }
}

function showToast(title, message) {
  const toast = document.querySelector('#app-toast');
  const heading = document.querySelector('#app-toast-title');
  const detail = document.querySelector('#app-toast-message');
  if (!(toast instanceof HTMLElement) || !heading || !detail) return;

  heading.textContent = title;
  detail.textContent = message;
  toast.hidden = false;

  const status = document.querySelector('#navigation-status');
  if (status) status.textContent = `${title}. ${message}`;

  if (toastTimer !== null) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(hideToast, TOAST_DURATION_MS);
}

function announceUnavailableRoute(label) {
  showToast(
    `${label} is coming later`,
    'This section is not available in the current pre-alpha build. Vault remains selected and no private data is loaded.',
  );
}

function announceLockedAction(label) {
  showToast(
    `${label} requires an unlocked vault`,
    'This build keeps the vault locked while end-to-end cryptography and interoperability are still under review.',
  );
}

function renderNavigationState() {
  const route = routeFromHash();
  const activeRoute = route === 'vault' || route === '' || route === 'main' || route === 'sign-in' || route === 'readiness'
    ? 'vault'
    : null;

  document.querySelectorAll('.nav-item').forEach((item) => {
    const itemRoute = item.getAttribute('href')?.replace(/^#/, '') ?? '';
    const active = itemRoute === activeRoute;
    item.classList.toggle('active', active);
    if (active) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });

  if (PREALPHA_DISABLED_ROUTES.has(route)) {
    const item = document.querySelector(`.nav-item[href="#${route}"]`);
    announceUnavailableRoute(item?.textContent?.trim() || route);
    history.replaceState(null, '', '#vault');
    renderNavigationState();
  }
}

function bindNavigation() {
  document.querySelectorAll('.nav-item[data-prealpha-disabled="true"]').forEach((item) => {
    item.addEventListener('click', (event) => {
      event.preventDefault();
      announceUnavailableRoute(item.textContent?.trim() || 'This section');
    });
  });

  document.querySelectorAll('[data-prealpha-action]').forEach((control) => {
    control.addEventListener('click', (event) => {
      event.preventDefault();
      announceLockedAction(control.getAttribute('data-prealpha-action') || 'This action');
    });
  });

  const dismiss = document.querySelector('#app-toast-dismiss');
  if (dismiss instanceof HTMLButtonElement) dismiss.addEventListener('click', hideToast);

  window.addEventListener('hashchange', renderNavigationState);
  renderNavigationState();
}

function bindSkipTarget() {
  const main = document.querySelector('#main');
  if (!main) return;
  main.addEventListener('focus', () => main.scrollIntoView({ block: 'start' }), { once: true });
}

function renderSecurityState(snapshot) {
  document.documentElement.dataset.sessionState = snapshot.status;
  document.documentElement.dataset.vaultLocked = String(snapshot.vaultLocked);

  const prealpha = document.querySelector('#prealpha-status');
  if (prealpha) {
    const origin = resolveServerOrigin();
    prealpha.textContent = snapshot.accountId
      ? `Account scoped · vault locked · ${origin}`
      : `Prelogin available · credential processing disabled · ${origin}`;
  }
}

function renderAuthState(snapshot) {
  document.documentElement.dataset.authPhase = snapshot.phase;
  const result = document.querySelector('#prelogin-result');
  if (!result) return;

  if (snapshot.phase === 'prelogin-pending') {
    result.textContent = 'Verifying the GoreeVault Server and checking account KDF settings. No password is being requested or processed.';
    return;
  }
  if (snapshot.phase === 'prelogin-ready' && snapshot.prelogin) {
    const kdfName = snapshot.prelogin.kdf === 0 ? 'PBKDF2' : 'Argon2id';
    const server = verifiedServerConfig ? `GoreeVault Server ${verifiedServerConfig.version}. ` : '';
    result.textContent = `${server}Account preparation succeeded. Server KDF: ${kdfName}. Password entry and cryptographic unlock remain disabled.`;
    return;
  }
  if (snapshot.phase === 'authentication-error') {
    result.textContent = 'Account preparation could not be completed. Verify the address and GoreeVault Server availability, then try again.';
    return;
  }
  result.textContent = 'No account has been checked yet.';
}

function bindPrelogin() {
  const form = document.querySelector('#prelogin-form');
  const input = document.querySelector('#account-email');
  const submit = document.querySelector('#prelogin-submit');
  if (!(form instanceof HTMLFormElement) || !(input instanceof HTMLInputElement) || !(submit instanceof HTMLButtonElement)) {
    return;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    input.setCustomValidity('');

    let email;
    try {
      email = normalizeAccountIdentifier(input.value);
    } catch (_) {
      input.setCustomValidity('Enter a valid GoreeVault account email address.');
      input.reportValidity();
      return;
    }

    const pending = beginPrelogin({ accountId: email, emailHint: email });
    submit.disabled = true;
    input.setAttribute('aria-busy', 'true');
    verifiedServerConfig = null;

    try {
      verifiedServerConfig = await requestServerConfig();
      const metadata = await requestPreloginMetadata(email);
      acceptPrelogin(metadata, pending.requestEpoch);
    } catch (error) {
      rejectAuthentication(error?.code ?? 'request_failed', pending.requestEpoch);
    } finally {
      submit.disabled = false;
      input.removeAttribute('aria-busy');
    }
  });
}

function assertPreAlphaSafety() {
  if (runtimeConfig.telemetryEnabled || runtimeConfig.credentialProcessingEnabled) {
    throw new Error('Pre-alpha runtime safety flags must remain disabled.');
  }
  if (cryptoBoundary.implementation !== 'unavailable-pre-alpha') {
    throw new Error('Unexpected cryptography implementation state.');
  }
  const snapshot = getSessionSnapshot();
  if (!snapshot.vaultLocked || snapshot.status !== 'signed-out') {
    throw new Error('Pre-alpha browser shell must initialize signed out and locked.');
  }
}

assertPreAlphaSafety();
subscribeSession(renderSecurityState);
subscribeAuth(renderAuthState);
bindAppearance();
bindNavigation();
bindSkipTarget();
bindPrelogin();
