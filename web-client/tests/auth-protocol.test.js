import test from 'node:test';
import assert from 'node:assert/strict';

import {
  normalizeAccountIdentifier,
  normalizePreloginMetadata,
  normalizeTwoFactorChallenge,
  tokenLifecycle,
} from '../assets/auth-protocol.js';
import {
  buildPasswordGrantEnvelope,
  buildSecretBearingPasswordGrant,
  createEphemeralBrowserDevice,
  PASSWORD_SCOPE,
  WEB_CLIENT_ID,
} from '../assets/auth-request.js';

test('account identifiers are trimmed and normalized', () => {
  assert.equal(normalizeAccountIdentifier('  USER@Example.COM  '), 'user@example.com');
  assert.throws(() => normalizeAccountIdentifier('not-an-email'), /valid account email/i);
});

test('prelogin metadata accepts supported KDF shapes and rejects unknown types', () => {
  assert.deepEqual(normalizePreloginMetadata({
    kdf: 0,
    kdfIterations: 600000,
    kdfMemory: null,
    kdfParallelism: null,
  }), {
    kdf: 0,
    kdfIterations: 600000,
    kdfMemory: null,
    kdfParallelism: null,
  });

  assert.throws(() => normalizePreloginMetadata({
    kdf: 99,
    kdfIterations: 1,
  }), /unsupported kdf/i);
});

test('two-factor challenges preserve provider identifiers and bounded metadata only', () => {
  const challenge = normalizeTwoFactorChallenge({
    error: 'invalid_grant',
    error_description: 'Two factor required.',
    TwoFactorProviders: ['0', '7'],
    TwoFactorProviders2: {
      '0': null,
      '7': { Email: 'u***@example.com' },
    },
  });

  assert.deepEqual(challenge.providers, [0, 7]);
  assert.deepEqual(challenge.providerMetadata['7'], { Email: 'u***@example.com' });
  assert.equal(challenge.kind, 'two-factor-required');
});

test('password grant envelope contains only non-secret compatible fields', () => {
  const device = createEphemeralBrowserDevice({
    identifier: '00000000-0000-4000-8000-000000000001',
    name: 'GoreeVault Web Test',
  });
  const envelope = buildPasswordGrantEnvelope({
    accountIdentifier: 'USER@example.com',
    device,
  });

  assert.equal(envelope.client_id, WEB_CLIENT_ID);
  assert.equal(envelope.scope, PASSWORD_SCOPE);
  assert.equal(envelope.username, 'user@example.com');
  assert.equal(envelope.device_type, '14');
  assert.equal('password' in envelope, false);
  assert.equal('two_factor_token' in envelope, false);
});

test('secret-bearing grants and token lifecycle stay fail-closed', () => {
  const device = createEphemeralBrowserDevice({
    identifier: '00000000-0000-4000-8000-000000000002',
  });

  assert.throws(() => buildSecretBearingPasswordGrant({
    accountIdentifier: 'user@example.com',
    device,
    passwordHash: 'never-used',
  }), /disabled/i);
  assert.throws(() => tokenLifecycle.acceptTokenSet({}), /unavailable|disabled/i);
  assert.equal(tokenLifecycle.persistentTokenStorageEnabled, false);
});
