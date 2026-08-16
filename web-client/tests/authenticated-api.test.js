import assert from 'node:assert/strict';
import test from 'node:test';

import { requestAuthenticatedApi } from '../assets/authenticated-api.js';
import { acceptInitialTokenSet, clearTokenState, getTokenSnapshot } from '../assets/token-state.js';

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

test('authenticated requests require the selected account token', async () => {
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 0 });
  await assert.rejects(
    () => requestAuthenticatedApi('/api/sync', { accountId: 'acct-b', now: 1000 }),
    /No usable access token exists/,
  );
});

test('authenticated requests attach bearer token without exposing it in state snapshots', async () => {
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 0 });

  const originalFetch = globalThis.fetch;
  let authorization = null;
  globalThis.fetch = async (_url, options) => {
    authorization = options.headers.get('Authorization');
    return {
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      async json() { return { object: 'sync' }; },
    };
  };
  try {
    const response = await requestAuthenticatedApi('/api/sync', {
      accountId: 'acct-a',
      now: 1000,
      locationOrigin: 'http://localhost:8080',
    });
    assert.equal(authorization, 'Bearer access-a');
    assert.equal(response.status, 200);
    assert.equal('accessToken' in getTokenSnapshot(), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('401 invalidates the memory-only token session', async () => {
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 0 });

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 401,
    headers: new Headers({ 'content-type': 'application/json' }),
    async json() { return { error: 'invalid_token' }; },
  });
  try {
    await assert.rejects(
      () => requestAuthenticatedApi('/api/sync', {
        accountId: 'acct-a',
        now: 1000,
        locationOrigin: 'http://localhost:8080',
      }),
      /invalid_token|authentication/i,
    );
    assert.equal(getTokenSnapshot().authenticated, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
