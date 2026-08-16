import test from 'node:test';
import assert from 'node:assert/strict';

import { normalizeSyncEnvelope, syncLifecycle } from '../assets/sync-protocol.js';
import {
  acceptOpaqueSync,
  beginVaultScope,
  clearVaultState,
  getVaultSnapshot,
  switchVaultAccount,
} from '../assets/vault-state.js';

function fixture() {
  return {
    object: 'sync',
    profile: { id: 'user-1', email: 'user@example.com' },
    folders: [],
    collections: [],
    policies: [],
    ciphers: [{ id: 'cipher-1', name: '2.encrypted-value' }],
    domains: null,
    sends: [],
    userDecryption: { masterPasswordUnlock: null },
  };
}

test('sync normalization requires the compatible GoreeVault envelope shape', () => {
  const sync = normalizeSyncEnvelope(fixture());
  assert.equal(sync.object, 'sync');
  assert.equal(sync.ciphers.length, 1);
  assert.equal(Object.isFrozen(sync), true);
  assert.equal(Object.isFrozen(sync.ciphers), true);
  assert.throws(() => normalizeSyncEnvelope({ object: 'sync', profile: {}, ciphers: [] }), /folders/i);
});

test('opaque sync state is account scoped and rejects stale or cross-account data', () => {
  clearVaultState();
  const first = beginVaultScope('one@example.com');
  const sync = normalizeSyncEnvelope(fixture());
  acceptOpaqueSync('one@example.com', sync, first.stateEpoch);
  assert.equal(getVaultSnapshot().phase, 'opaque-sync-ready');

  const second = switchVaultAccount('two@example.com');
  assert.equal(second.sync, null);
  assert.throws(() => acceptOpaqueSync('one@example.com', sync, second.stateEpoch), /cross-account/i);
  assert.throws(() => acceptOpaqueSync('two@example.com', sync, first.stateEpoch), /stale/i);
});

test('authenticated sync and persistent cache remain disabled', () => {
  assert.equal(syncLifecycle.authenticatedSyncEnabled, false);
  assert.equal(syncLifecycle.persistentEncryptedCacheEnabled, false);
  assert.throws(() => syncLifecycle.requestAuthenticatedSync(), /unavailable/i);
});
