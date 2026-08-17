import assert from 'node:assert/strict';
import test from 'node:test';

import {
  acceptInitialTokenSet,
  acceptRotatedTokenSet,
  beginRefresh,
  clearTokenState,
  getTokenSnapshot,
  isAccessTokenUsable,
  readAccessTokenForAccount,
} from '../assets/token-state.js';

function tokenSet({ access = 'access-a', refresh = 'refresh-a', expiresIn = 7200 } = {}) {
  return {
    kind: 'authenticated',
    accessToken: access,
    refreshToken: refresh,
    expiresIn,
    tokenType: 'Bearer',
    scope: 'api offline_access',
  };
}

test('tokens remain memory-only and account-scoped', () => {
  clearTokenState();
  const snapshot = acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 1000 });
  assert.equal(snapshot.authenticated, true);
  assert.equal(snapshot.storage, 'memory-only');
  assert.equal(readAccessTokenForAccount('acct-a'), 'access-a');
  assert.throws(() => readAccessTokenForAccount('acct-b'), /No access token exists/);
  assert.equal('accessToken' in snapshot, false);
  assert.equal('refreshToken' in snapshot, false);
});

test('access-token usability accounts for expiry skew', () => {
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet({ expiresIn: 60 }), now: 1000 });
  assert.equal(isAccessTokenUsable({ accountId: 'acct-a', now: 1000, clockSkewMs: 30000 }), true);
  assert.equal(isAccessTokenUsable({ accountId: 'acct-a', now: 31001, clockSkewMs: 30000 }), false);
});

test('refresh acceptance requires rotation and current generation', () => {
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 1000 });
  const request = beginRefresh({ accountId: 'acct-a', now: 2000 });
  const updated = acceptRotatedTokenSet({
    refreshRequest: request,
    tokenSet: tokenSet({ access: 'access-b', refresh: 'refresh-b' }),
    now: 3000,
  });
  assert.equal(updated.authenticated, true);
  assert.equal(readAccessTokenForAccount('acct-a'), 'access-b');
  assert.throws(() => acceptRotatedTokenSet({
    refreshRequest: request,
    tokenSet: tokenSet({ access: 'access-c', refresh: 'refresh-c' }),
  }), /Stale refresh response rejected/);
});

test('non-rotating refresh token invalidates the session', () => {
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 1000 });
  const request = beginRefresh({ accountId: 'acct-a', now: 2000 });
  assert.throws(() => acceptRotatedTokenSet({
    refreshRequest: request,
    tokenSet: tokenSet({ access: 'access-b', refresh: 'refresh-a' }),
    now: 3000,
  }), /session invalidated/);
  assert.equal(getTokenSnapshot().authenticated, false);
});

test('account changes reject refresh-token replay', () => {
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-a', tokenSet: tokenSet(), now: 1000 });
  const request = beginRefresh({ accountId: 'acct-a', now: 2000 });
  clearTokenState();
  acceptInitialTokenSet({ accountId: 'acct-b', tokenSet: tokenSet({ access: 'b', refresh: 'b-refresh' }), now: 3000 });
  assert.throws(() => acceptRotatedTokenSet({
    refreshRequest: request,
    tokenSet: tokenSet({ access: 'old', refresh: 'old-refresh' }),
  }), /Stale refresh response rejected/);
});
