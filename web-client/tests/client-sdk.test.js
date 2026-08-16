import test from 'node:test';
import assert from 'node:assert/strict';

import { createGoreeVaultClient, clientSdkBoundary } from '../assets/client-sdk.js';
import { beginAccountSession } from '../assets/session-state.js';
import { beginVaultScope } from '../assets/vault-state.js';

const SERVER = Object.freeze({
  name: 'GoreeVault',
  version: 'test',
  vault: 'https://vault.goreecloud.com',
  api: 'https://vault.goreecloud.com/api',
  identity: 'https://vault.goreecloud.com/identity',
  notifications: 'https://vault.goreecloud.com/notifications',
  suppressOnboardingInterstitials: true,
});

const PRELOGIN = Object.freeze({
  kdf: 0,
  kdfIterations: 600000,
  kdfMemory: null,
  kdfParallelism: null,
});

function clientWith(overrides = {}) {
  return createGoreeVaultClient({
    serverConfigRequest: async () => SERVER,
    preloginRequest: async () => PRELOGIN,
    syncRequest: async () => Object.freeze({ phase: 'opaque-sync-ready' }),
    ...overrides,
  });
}

test('SDK boundary remains fail-closed for production credential handling', () => {
  assert.equal(clientSdkBoundary.serverVerificationRequiredBeforePrelogin, true);
  assert.equal(clientSdkBoundary.credentialProcessingEnabled, false);
  assert.equal(clientSdkBoundary.passwordInputEnabled, false);
  assert.equal(clientSdkBoundary.tokenExchangeEnabled, false);
  assert.equal(clientSdkBoundary.decryptedVaultPresentationEnabled, false);
  assert.equal(clientSdkBoundary.persistentCredentialStorageEnabled, false);
});

test('prepareAccount verifies server before prelogin and normalizes account scope', async () => {
  const calls = [];
  const client = clientWith({
    serverConfigRequest: async () => {
      calls.push('server-config');
      return SERVER;
    },
    preloginRequest: async (accountId) => {
      calls.push(`prelogin:${accountId}`);
      return PRELOGIN;
    },
  });
  client.reset();

  const prepared = await client.prepareAccount(' User@Example.COM ');
  assert.deepEqual(calls, ['server-config', 'prelogin:user@example.com']);
  assert.equal(prepared.accountId, 'user@example.com');
  assert.equal(prepared.server.name, 'GoreeVault');
  assert.equal(prepared.prelogin.kdf, 0);

  const snapshot = client.getSnapshot();
  assert.equal(snapshot.server.version, 'test');
  assert.equal(snapshot.authentication.accountId, 'user@example.com');
  assert.equal(snapshot.authentication.phase, 'prelogin-ready');
  assert.equal(snapshot.session.status, 'signed-out');
  assert.equal(snapshot.tokens.authenticated, false);
  assert.equal(snapshot.vault.phase, 'empty');
  client.reset();
});

test('prepareAccount fails closed when server verification fails', async () => {
  let preloginCalled = false;
  const failure = Object.assign(new Error('Unexpected server identity.'), { code: 'server_identity' });
  const client = clientWith({
    serverConfigRequest: async () => { throw failure; },
    preloginRequest: async () => {
      preloginCalled = true;
      return PRELOGIN;
    },
  });
  client.reset();

  await assert.rejects(client.prepareAccount('user@example.com'), /Unexpected server identity/);
  assert.equal(preloginCalled, false);
  const snapshot = client.getSnapshot();
  assert.equal(snapshot.server, null);
  assert.equal(snapshot.authentication.phase, 'authentication-error');
  assert.equal(snapshot.authentication.lastErrorCode, 'server_identity');
  client.reset();
});

test('syncAccount rejects missing authenticated account scope before transport', async () => {
  let syncCalls = 0;
  const client = clientWith({
    syncRequest: async () => {
      syncCalls += 1;
      return Object.freeze({ phase: 'opaque-sync-ready' });
    },
  });
  client.reset();

  await assert.rejects(client.syncAccount('user@example.com'), /No authenticated session/);
  assert.equal(syncCalls, 0);
  client.reset();
});

test('syncAccount delegates only after matching session and vault scopes exist', async () => {
  const observed = [];
  const client = clientWith({
    syncRequest: async (accountId, options) => {
      observed.push({ accountId, options });
      return Object.freeze({ phase: 'opaque-sync-ready', accountId });
    },
  });
  client.reset();
  beginAccountSession({ accountId: 'user@example.com', emailHint: 'user@example.com' });
  beginVaultScope('user@example.com');

  const result = await client.syncAccount('USER@example.com', { timeoutMs: 9000 });
  assert.equal(result.phase, 'opaque-sync-ready');
  assert.deepEqual(observed, [{ accountId: 'user@example.com', options: { timeoutMs: 9000 } }]);
  client.reset();
});

test('reset clears verified server and all in-memory client scopes', async () => {
  const client = clientWith();
  client.reset();
  await client.prepareAccount('user@example.com');
  beginAccountSession({ accountId: 'user@example.com', emailHint: 'user@example.com' });
  beginVaultScope('user@example.com');

  const reset = client.reset();
  assert.equal(reset.server, null);
  assert.equal(reset.authentication.phase, 'signed-out');
  assert.equal(reset.session.status, 'signed-out');
  assert.equal(reset.tokens.authenticated, false);
  assert.equal(reset.vault.phase, 'empty');
});
