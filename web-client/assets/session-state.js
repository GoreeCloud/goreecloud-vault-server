const EMPTY = Object.freeze({
  accountId: null,
  emailHint: null,
  status: 'signed-out',
  vaultLocked: true,
  sessionEpoch: 0,
});

let state = { ...EMPTY };
const listeners = new Set();

function publish() {
  const snapshot = Object.freeze({ ...state });
  for (const listener of listeners) listener(snapshot);
  return snapshot;
}

export function getSessionSnapshot() {
  return Object.freeze({ ...state });
}

export function subscribeSession(listener) {
  if (typeof listener !== 'function') throw new TypeError('Session listener must be a function.');
  listeners.add(listener);
  listener(getSessionSnapshot());
  return () => listeners.delete(listener);
}

export function beginAccountSession({ accountId, emailHint = null } = {}) {
  if (!accountId || typeof accountId !== 'string') {
    throw new TypeError('An explicit account identifier is required.');
  }
  state = {
    accountId,
    emailHint,
    status: 'authenticated-locked',
    vaultLocked: true,
    sessionEpoch: state.sessionEpoch + 1,
  };
  return publish();
}

export function markVaultUnlocked() {
  if (!state.accountId || state.status === 'signed-out') {
    throw new Error('Cannot unlock without an account-scoped authenticated session.');
  }
  state = { ...state, status: 'authenticated-unlocked', vaultLocked: false };
  return publish();
}

export function lockVault() {
  if (!state.accountId) return getSessionSnapshot();
  state = { ...state, status: 'authenticated-locked', vaultLocked: true };
  return publish();
}

export function clearSession() {
  state = { ...EMPTY, sessionEpoch: state.sessionEpoch + 1 };
  return publish();
}

export function switchAccount(nextAccount) {
  clearSession();
  return beginAccountSession(nextAccount);
}
