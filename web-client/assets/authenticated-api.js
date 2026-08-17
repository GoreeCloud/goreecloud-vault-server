import { requestApi } from './api-client.js';
import {
  clearTokenState,
  isAccessTokenUsable,
  readAccessTokenForAccount,
} from './token-state.js';

function requireAccountId(accountId) {
  if (typeof accountId !== 'string' || accountId.length === 0) throw new TypeError('Account identifier is required.');
  return accountId;
}

export async function requestAuthenticatedApi(path, {
  accountId,
  headers = {},
  now = Date.now(),
  clockSkewMs = 30000,
  ...options
} = {}) {
  const selectedAccount = requireAccountId(accountId);
  if (!isAccessTokenUsable({ accountId: selectedAccount, now, clockSkewMs })) {
    throw new Error('No usable access token exists for the selected account.');
  }

  const token = readAccessTokenForAccount(selectedAccount);
  const requestHeaders = new Headers(headers);
  requestHeaders.set('Authorization', `Bearer ${token}`);

  try {
    return await requestApi(path, {
      ...options,
      headers: requestHeaders,
    });
  } catch (error) {
    if (error?.code === 'authentication_required' || error?.status === 401) clearTokenState();
    throw error;
  }
}
