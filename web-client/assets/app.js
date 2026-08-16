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
let verifiedServerConfig = null;

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
bindSkipTarget();
bindPrelogin();
