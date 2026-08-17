const INITIAL = Object.freeze({
  accountId: null,
  accessToken: null,
  refreshToken: null,
  tokenType: null,
  scope: null,
  accessExpiresAt: null,
  generation: 0,
});

let tokenState = { ...INITIAL };

function requireAccountId(accountId) {
  if (typeof accountId !== 'string' || accountId.length === 0) throw new TypeError('Account identifier is required.');
  return accountId;
}

function requireToken(value, field) {
  if (typeof value !== 'string' || value.length === 0 || value.length > 16384) throw new TypeError(`Invalid ${field}.`);
  return value;
}

function snapshot() {
  return Object.freeze({
    accountId: tokenState.accountId,
    authenticated: Boolean(tokenState.accessToken && tokenState.refreshToken),
    tokenType: tokenState.tokenType,
    scope: tokenState.scope,
    accessExpiresAt: tokenState.accessExpiresAt,
    generation: tokenState.generation,
    storage: 'memory-only',
  });
}

export function getTokenSnapshot() {
  return snapshot();
}

export function clearTokenState() {
  tokenState = { ...INITIAL, generation: tokenState.generation + 1 };
  return snapshot();
}

export function acceptInitialTokenSet({ accountId, tokenSet, now = Date.now() } = {}) {
  const normalizedAccountId = requireAccountId(accountId);
  if (!tokenSet || tokenSet.kind !== 'authenticated') throw new TypeError('Validated authenticated token set is required.');
  if (!Number.isFinite(now)) throw new TypeError('Current time is required.');

  tokenState = {
    accountId: normalizedAccountId,
    accessToken: requireToken(tokenSet.accessToken, 'access token'),
    refreshToken: requireToken(tokenSet.refreshToken, 'refresh token'),
    tokenType: tokenSet.tokenType,
    scope: tokenSet.scope,
    accessExpiresAt: now + (tokenSet.expiresIn * 1000),
    generation: tokenState.generation + 1,
  };
  return snapshot();
}

export function beginRefresh({ accountId, now = Date.now() } = {}) {
  const normalizedAccountId = requireAccountId(accountId);
  if (normalizedAccountId !== tokenState.accountId || !tokenState.refreshToken) {
    throw new Error('No refresh token exists for the selected account.');
  }
  if (!Number.isFinite(now)) throw new TypeError('Current time is required.');
  return Object.freeze({
    accountId: tokenState.accountId,
    refreshToken: tokenState.refreshToken,
    expectedGeneration: tokenState.generation,
    requestedAt: now,
  });
}

export function acceptRotatedTokenSet({ refreshRequest, tokenSet, now = Date.now() } = {}) {
  if (!refreshRequest || typeof refreshRequest !== 'object') throw new TypeError('Refresh request context is required.');
  if (!tokenSet || tokenSet.kind !== 'authenticated') throw new TypeError('Validated authenticated token set is required.');
  if (refreshRequest.accountId !== tokenState.accountId || refreshRequest.expectedGeneration !== tokenState.generation) {
    throw new Error('Stale refresh response rejected.');
  }
  if (refreshRequest.refreshToken !== tokenState.refreshToken) throw new Error('Refresh-token replay rejected.');

  const nextRefreshToken = requireToken(tokenSet.refreshToken, 'refresh token');
  if (nextRefreshToken === tokenState.refreshToken) {
    clearTokenState();
    throw new Error('Refresh token did not rotate; session invalidated.');
  }

  return acceptInitialTokenSet({ accountId: tokenState.accountId, tokenSet, now });
}

export function isAccessTokenUsable({ accountId, now = Date.now(), clockSkewMs = 30000 } = {}) {
  if (accountId !== tokenState.accountId || !tokenState.accessToken || !Number.isFinite(tokenState.accessExpiresAt)) return false;
  if (!Number.isFinite(now) || !Number.isFinite(clockSkewMs) || clockSkewMs < 0) return false;
  return now + clockSkewMs < tokenState.accessExpiresAt;
}

export function readAccessTokenForAccount(accountId) {
  if (accountId !== tokenState.accountId || !tokenState.accessToken) throw new Error('No access token exists for the selected account.');
  return tokenState.accessToken;
}
