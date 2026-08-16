import { requestAuthenticatedApi } from './authenticated-api.js';
import { normalizeSyncEnvelope } from './sync-protocol.js';
import { acceptOpaqueSync, getVaultSnapshot } from './vault-state.js';

export async function requestAccountSync(accountId, options = {}) {
  const snapshot = getVaultSnapshot();
  if (snapshot.accountId !== accountId) throw new Error('Vault scope does not match the selected account.');
  const expectedEpoch = snapshot.stateEpoch;

  const response = await requestAuthenticatedApi('/api/sync', {
    ...options,
    accountId,
    method: 'GET',
  });
  const envelope = normalizeSyncEnvelope(response.payload);
  return acceptOpaqueSync(accountId, envelope, expectedEpoch);
}
