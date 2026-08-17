import assert from 'node:assert/strict';
import test from 'node:test';

import {
  encodeIdentityForm,
  identityProtocol,
  normalizeIdentityResponse,
  normalizeIdentitySuccess,
  requestIdentityToken,
} from '../assets/identity-protocol.js';

test('identity form uses the compatible x-www-form-urlencoded shape', () => {
  const encoded = encodeIdentityForm({
    grant_type: 'password',
    client_id: 'web',
    scope: 'api offline_access',
    username: 'user@example.com',
    password: 'hash+/=',
  });
  const parsed = new URLSearchParams(encoded);
  assert.equal(parsed.get('grant_type'), 'password');
  assert.equal(parsed.get('client_id'), 'web');
  assert.equal(parsed.get('scope'), 'api offline_access');
  assert.equal(parsed.get('password'), 'hash+/=');
});

test('successful token responses are normalized without persistence', () => {
  const result = normalizeIdentitySuccess({
    access_token: 'access-token',
    refresh_token: 'refresh-token',
    expires_in: 7200,
    token_type: 'Bearer',
    scope: 'api offline_access',
  });
  assert.deepEqual(result, {
    kind: 'authenticated',
    accessToken: 'access-token',
    refreshToken: 'refresh-token',
    expiresIn: 7200,
    tokenType: 'Bearer',
    scope: 'api offline_access',
  });
});

test('successful token responses reject unsupported token types and scopes', () => {
  assert.throws(() => normalizeIdentitySuccess({
    access_token: 'a', refresh_token: 'r', expires_in: 1, token_type: 'MAC', scope: 'api',
  }), /Unsupported identity token type/);
  assert.throws(() => normalizeIdentitySuccess({
    access_token: 'a', refresh_token: 'r', expires_in: 1, token_type: 'Bearer', scope: 'offline_access',
  }), /does not include api/);
});

test('two-factor challenges are routed through the compatible challenge normalizer', () => {
  const result = normalizeIdentityResponse({
    status: 400,
    payload: {
      error: 'invalid_grant',
      error_description: 'Two factor required.',
      TwoFactorProviders: ['0'],
      TwoFactorProviders2: { '0': null },
    },
  });
  assert.deepEqual(result, { kind: 'two-factor-required', providers: [0], providerMetadata: { '0': null } });
});

test('ordinary identity failures expose only bounded status/error state', () => {
  assert.deepEqual(
    normalizeIdentityResponse({ status: 400, payload: { error: 'invalid_grant', error_description: 'secret detail' } }),
    { kind: 'rejected', status: 400, error: 'invalid_grant' },
  );
});

test('network token exchange stays fail-closed before credential processing approval', async () => {
  await assert.rejects(
    () => requestIdentityToken({ grant_type: 'password' }, { fetchImpl: async () => { throw new Error('must not execute'); } }),
    /disabled until credential processing is approved/,
  );
  assert.equal(identityProtocol.tokenPath, '/identity/connect/token');
  assert.equal(identityProtocol.contentType, 'application/x-www-form-urlencoded');
  assert.equal(identityProtocol.credentialProcessingEnabled, false);
});
