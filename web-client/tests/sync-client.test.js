import assert from 'node:assert/strict';
import test from 'node:test';

import { requestAccountSync } from '../assets/sync-client.js';
import { acceptInitialTokenSet, clearTokenState } from '../assets/token-state.js';
import { beginVaultScope, clearVaultState, getVaultSnapshot } from '../assets/vault-state.js';

function tokenSet() {
  return {
    kind: 'authenticated',
    accessToken: 'access-a',
    refreshToken: 'refresh-a',
    expiresIn: 7200,
    tokenType: 'Bearer',
    scope: 'api offline_access',
  };
}

function syncEnvelope() {
  return {
    object: 'sync',
    profile: { id: 'profile-a' },
    folders: [],
    collections: [],
    policies: [],
    ciphers: [],
    domains: null,
    sends: [],
    userDecryption: { masterPasswordUnlock: null },
  };
}

test('authenticated sync requires matching vault and token account scope', async () => {
  clearTokenState();
  clearVaultState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 0 });
  beginVaultScope('acct-b');
  await assert.rejects(() => requestAccountSync('acct-a', { now: 1000 }), /Vault scope does not match/);
});

test('authenticated sync stores only the validated opaque account envelope', async () => {
  clearTokenState();
  clearVaultState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 0 });
  beginVaultScope('acct-a');

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'application/json' }),
    async json() { return syncEnvelope(); },
  });
  try {
    const result = await requestAccountSync('acct-a', {
      now: 1000,
      locationOrigin: 'http://localhost:8080',
    });
    assert.equal(result.phase, 'opaque-sync-ready');
    assert.equal(result.accountId, 'acct-a');
    assert.equal(result.sync.object, 'sync');
    assert.equal(getVaultSnapshot().sync.profile.id, 'profile-a');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('vault epoch changes reject a stale in-flight sync response', async () => {
  clearTokenState();
  clearVaultState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 0 });
  beginVaultScope('acct-a');

  const originalFetch = globalThis.fetch;
  let release;
  const waiting = new Promise((resolve) => { release = resolve; });
  globalThis.fetch = async () => {
    await waiting;
    return {
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      async json() { return syncEnvelope(); },
    };
  };
  try {
    const pending = requestAccountSync('acct-a', {
      now: 1000,
      locationOrigin: 'http://localhost:8080',
    });
    clearVaultState();
    beginVaultScope('acct-a');
    release();
    await assert.rejects(() => pending, /Stale vault sync state rejected/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
