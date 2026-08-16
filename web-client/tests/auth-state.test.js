import test from 'node:test';
import assert from 'node:assert/strict';

import {
  acceptPrelogin,
  beginPrelogin,
  clearAuthentication,
  getAuthSnapshot,
  rejectAuthentication,
  switchAuthenticationAccount,
} from '../assets/auth-state.js';

test('authentication starts signed out and clears account state', () => {
  clearAuthentication();
  const state = getAuthSnapshot();
  assert.equal(state.accountId, null);
  assert.equal(state.phase, 'signed-out');
  assert.equal(state.prelogin, null);
});

test('prelogin acceptance is bound to the active request epoch', () => {
  clearAuthentication();
  const first = beginPrelogin({ accountId: 'one@example.com' });
  const staleEpoch = first.requestEpoch;
  const second = switchAuthenticationAccount({ accountId: 'two@example.com' });

  assert.notEqual(second.requestEpoch, staleEpoch);
  assert.throws(() => acceptPrelogin({ kdf: 0, kdfIterations: 1 }, staleEpoch), /stale/i);

  const accepted = acceptPrelogin({ kdf: 0, kdfIterations: 600000 }, second.requestEpoch);
  assert.equal(accepted.accountId, 'two@example.com');
  assert.equal(accepted.phase, 'prelogin-ready');
});

test('stale failures cannot overwrite a newer account request', () => {
  clearAuthentication();
  const oldRequest = beginPrelogin({ accountId: 'old@example.com' });
  const current = switchAuthenticationAccount({ accountId: 'current@example.com' });

  const afterStaleFailure = rejectAuthentication('network_error', oldRequest.requestEpoch);
  assert.equal(afterStaleFailure.accountId, 'current@example.com');
  assert.equal(afterStaleFailure.phase, 'prelogin-pending');
  assert.equal(afterStaleFailure.requestEpoch, current.requestEpoch);
});
