import { requestApi } from './api-client.js';
import { runtimeConfig } from './runtime-config.js';

const KDF_TYPES = new Set([0, 1]);

function requireInteger(value, field, { min = 1, allowNull = false } = {}) {
  if (allowNull && (value === null || value === undefined)) return null;
  if (!Number.isInteger(value) || value < min) throw new TypeError(`Invalid ${field} value.`);
  return value;
}

export function normalizeAccountIdentifier(value) {
  if (typeof value !== 'string') throw new TypeError('Account identifier must be a string.');
  const normalized = value.trim().toLowerCase();
  if (!normalized || normalized.length > 254 || !normalized.includes('@')) {
    throw new TypeError('A valid account email identifier is required.');
  }
  return normalized;
}

export function normalizePreloginMetadata(payload) {
  if (!payload || typeof payload !== 'object') throw new TypeError('Invalid prelogin response.');

  const kdf = requireInteger(payload.kdf, 'kdf', { min: 0 });
  if (!KDF_TYPES.has(kdf)) throw new TypeError('Unsupported KDF type.');

  return Object.freeze({
    kdf,
    kdfIterations: requireInteger(payload.kdfIterations, 'kdfIterations'),
    kdfMemory: requireInteger(payload.kdfMemory, 'kdfMemory', { allowNull: true }),
    kdfParallelism: requireInteger(payload.kdfParallelism, 'kdfParallelism', { allowNull: true }),
  });
}

export async function requestPreloginMetadata(accountIdentifier, options = {}) {
  const email = normalizeAccountIdentifier(accountIdentifier);
  const response = await requestApi('/api/accounts/prelogin', {
    ...options,
    method: 'POST',
    body: { email },
  });
  return normalizePreloginMetadata(response.payload);
}

export const tokenLifecycle = Object.freeze({
  storage: 'memory-only-pre-alpha',
  refreshRotationRequired: true,
  replayRejectionRequired: true,
  persistentTokenStorageEnabled: false,
  acceptTokenSet() {
    if (!runtimeConfig.credentialProcessingEnabled) {
      throw new Error('Token acceptance is unavailable while credential processing is disabled.');
    }
    throw new Error('Token lifecycle implementation is not available in this pre-alpha slice.');
  },
  refresh() {
    throw new Error('Refresh-token exchange is not available in this pre-alpha slice.');
  },
  revoke() {
    throw new Error('Session revocation is not available in this pre-alpha slice.');
  },
});
