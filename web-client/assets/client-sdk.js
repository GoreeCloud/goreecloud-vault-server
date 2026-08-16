import { normalizeAccountIdentifier, requestPreloginMetadata } from './auth-protocol.js';
import {
  acceptPrelogin,
  beginPrelogin,
  clearAuthentication,
  getAuthSnapshot,
  rejectAuthentication,
} from './auth-state.js';
import { runtimeConfig } from './runtime-config.js';
import { requestServerConfig } from './server-config.js';
import { clearSession, getSessionSnapshot } from './session-state.js';
import { requestAccountSync } from './sync-client.js';
import { clearTokenState, getTokenSnapshot } from './token-state.js';
import { clearVaultState, getVaultSnapshot } from './vault-state.js';

function requireFunction(value, field) {
  if (typeof value !== 'function') throw new TypeError(`${field} must be a function.`);
  return value;
}

function errorCode(error) {
  return typeof error?.code === 'string' && error.code ? error.code : 'request_failed';
}

function snapshotServer(server) {
  return server && typeof server === 'object' ? Object.freeze({ ...server }) : null;
}

function buildSnapshot(server) {
  return Object.freeze({
    server: snapshotServer(server),
    authentication: getAuthSnapshot(),
    session: getSessionSnapshot(),
    tokens: getTokenSnapshot(),
    vault: getVaultSnapshot(),
  });
}

export const clientSdkBoundary = Object.freeze({
  mode: 'pre-alpha-account-and-sync-facade',
  serverVerificationRequiredBeforePrelogin: true,
  credentialProcessingEnabled: runtimeConfig.credentialProcessingEnabled,
  passwordInputEnabled: false,
  tokenExchangeEnabled: false,
  decryptedVaultPresentationEnabled: false,
  persistentCredentialStorageEnabled: false,
});

export function createGoreeVaultClient({
  serverConfigRequest = requestServerConfig,
  preloginRequest = requestPreloginMetadata,
  syncRequest = requestAccountSync,
} = {}) {
  const requestConfig = requireFunction(serverConfigRequest, 'Server-config request');
  const requestPrelogin = requireFunction(preloginRequest, 'Prelogin request');
  const requestSync = requireFunction(syncRequest, 'Sync request');
  let verifiedServer = null;

  function reset() {
    clearTokenState();
    clearVaultState();
    clearSession();
    clearAuthentication();
    verifiedServer = null;
    return buildSnapshot(verifiedServer);
  }

  return Object.freeze({
    boundary: clientSdkBoundary,
    normalizeAccountIdentifier,

    getSnapshot() {
      return buildSnapshot(verifiedServer);
    },

    async prepareAccount(accountIdentifier, options = {}) {
      const accountId = normalizeAccountIdentifier(accountIdentifier);
      const pending = beginPrelogin({ accountId, emailHint: accountId });
      verifiedServer = null;

      try {
        const server = await requestConfig(options);
        const prelogin = await requestPrelogin(accountId, options);
        const authentication = acceptPrelogin(prelogin, pending.requestEpoch);
        verifiedServer = snapshotServer(server);
        return Object.freeze({
          accountId,
          server: snapshotServer(verifiedServer),
          prelogin: authentication.prelogin,
          requestEpoch: authentication.requestEpoch,
        });
      } catch (error) {
        rejectAuthentication(errorCode(error), pending.requestEpoch);
        throw error;
      }
    },

    async syncAccount(accountIdentifier, options = {}) {
      const accountId = normalizeAccountIdentifier(accountIdentifier);
      const session = getSessionSnapshot();
      const vault = getVaultSnapshot();

      if (session.accountId !== accountId || session.status === 'signed-out') {
        throw new Error('No authenticated session exists for the selected account.');
      }
      if (vault.accountId !== accountId) {
        throw new Error('No vault scope exists for the selected account.');
      }

      return requestSync(accountId, options);
    },

    reset,
  });
}
