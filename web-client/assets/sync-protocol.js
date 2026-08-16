import { runtimeConfig } from './runtime-config.js';

const REQUIRED_ARRAYS = ['folders', 'collections', 'policies', 'ciphers', 'sends'];

function cloneJsonValue(value) {
  if (value === null || typeof value !== 'object') return value;
  if (Array.isArray(value)) return value.map(cloneJsonValue);
  const output = {};
  for (const [key, child] of Object.entries(value)) output[key] = cloneJsonValue(child);
  return output;
}

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value)) deepFreeze(child);
  }
  return value;
}

export function normalizeSyncEnvelope(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new TypeError('Invalid vault sync response.');
  }
  if (payload.object !== 'sync') throw new TypeError('Response is not a vault sync envelope.');
  if (!payload.profile || typeof payload.profile !== 'object' || Array.isArray(payload.profile)) {
    throw new TypeError('Vault sync profile is required.');
  }
  for (const field of REQUIRED_ARRAYS) {
    if (!Array.isArray(payload[field])) throw new TypeError(`Vault sync ${field} must be an array.`);
  }
  if (!payload.userDecryption || typeof payload.userDecryption !== 'object' || Array.isArray(payload.userDecryption)) {
    throw new TypeError('Vault sync user-decryption metadata is required.');
  }

  const copy = cloneJsonValue({
    object: 'sync',
    profile: payload.profile,
    folders: payload.folders,
    collections: payload.collections,
    policies: payload.policies,
    ciphers: payload.ciphers,
    domains: payload.domains ?? null,
    sends: payload.sends,
    userDecryption: payload.userDecryption,
  });
  return deepFreeze(copy);
}

export const syncLifecycle = Object.freeze({
  storage: 'account-scoped-memory-only-pre-alpha',
  authenticatedSyncEnabled: false,
  persistentEncryptedCacheEnabled: false,
  requestAuthenticatedSync() {
    if (!runtimeConfig.credentialProcessingEnabled) {
      throw new Error('Authenticated sync is unavailable while credential processing is disabled.');
    }
    throw new Error('Authenticated sync transport is not available in this pre-alpha slice.');
  },
});
