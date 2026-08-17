const INITIAL = Object.freeze({
  accountId: null,
  phase: 'empty',
  sync: null,
  stateEpoch: 0,
});

let vaultState = { ...INITIAL };
const listeners = new Set();

function snapshot() {
  return Object.freeze({ ...vaultState });
}

function publish() {
  const next = snapshot();
  for (const listener of listeners) listener(next);
  return next;
}

export function getVaultSnapshot() {
  return snapshot();
}

export function subscribeVault(listener) {
  if (typeof listener !== 'function') throw new TypeError('Vault listener must be a function.');
  listeners.add(listener);
  listener(snapshot());
  return () => listeners.delete(listener);
}

export function beginVaultScope(accountId) {
  if (typeof accountId !== 'string' || !accountId) throw new TypeError('Account identifier is required.');
  vaultState = {
    accountId,
    phase: 'scoped-empty',
    sync: null,
    stateEpoch: vaultState.stateEpoch + 1,
  };
  return publish();
}

export function acceptOpaqueSync(accountId, syncEnvelope, expectedEpoch = vaultState.stateEpoch) {
  if (accountId !== vaultState.accountId) throw new Error('Cross-account sync state rejected.');
  if (expectedEpoch !== vaultState.stateEpoch) throw new Error('Stale vault sync state rejected.');
  if (!syncEnvelope || syncEnvelope.object !== 'sync') throw new TypeError('Validated sync envelope is required.');

  vaultState = {
    ...vaultState,
    phase: 'opaque-sync-ready',
    sync: syncEnvelope,
  };
  return publish();
}

export function clearVaultState() {
  vaultState = { ...INITIAL, stateEpoch: vaultState.stateEpoch + 1 };
  return publish();
}

export function switchVaultAccount(accountId) {
  clearVaultState();
  return beginVaultScope(accountId);
}
