const INITIAL = Object.freeze({
  accountId: null,
  emailHint: null,
  phase: 'signed-out',
  prelogin: null,
  requestEpoch: 0,
  lastErrorCode: null,
});

let authState = { ...INITIAL };
const listeners = new Set();

function snapshot() {
  return Object.freeze({
    ...authState,
    prelogin: authState.prelogin ? Object.freeze({ ...authState.prelogin }) : null,
  });
}

function publish() {
  const next = snapshot();
  for (const listener of listeners) listener(next);
  return next;
}

export function getAuthSnapshot() {
  return snapshot();
}

export function subscribeAuth(listener) {
  if (typeof listener !== 'function') throw new TypeError('Authentication listener must be a function.');
  listeners.add(listener);
  listener(snapshot());
  return () => listeners.delete(listener);
}

export function beginPrelogin({ accountId, emailHint = null } = {}) {
  if (typeof accountId !== 'string' || !accountId) throw new TypeError('Account identifier is required.');
  authState = {
    accountId,
    emailHint,
    phase: 'prelogin-pending',
    prelogin: null,
    requestEpoch: authState.requestEpoch + 1,
    lastErrorCode: null,
  };
  return publish();
}

export function acceptPrelogin(metadata, expectedEpoch = authState.requestEpoch) {
  if (!authState.accountId || authState.phase !== 'prelogin-pending') {
    throw new Error('No account-scoped prelogin request is active.');
  }
  if (expectedEpoch !== authState.requestEpoch) throw new Error('Stale prelogin response rejected.');
  if (!metadata || typeof metadata !== 'object') throw new TypeError('Prelogin metadata is required.');

  authState = { ...authState, phase: 'prelogin-ready', prelogin: { ...metadata }, lastErrorCode: null };
  return publish();
}

export function rejectAuthentication(errorCode = 'request_failed', expectedEpoch = authState.requestEpoch) {
  if (expectedEpoch !== authState.requestEpoch) return snapshot();
  authState = {
    ...authState,
    phase: authState.accountId ? 'authentication-error' : 'signed-out',
    prelogin: null,
    lastErrorCode: typeof errorCode === 'string' ? errorCode : 'request_failed',
  };
  return publish();
}

export function clearAuthentication() {
  authState = { ...INITIAL, requestEpoch: authState.requestEpoch + 1 };
  return publish();
}

export function switchAuthenticationAccount(nextAccount) {
  clearAuthentication();
  return beginPrelogin(nextAccount);
}
