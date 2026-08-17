import { requestApi } from './api-client.js';
import { runtimeConfig } from './runtime-config.js';

const KDF_TYPES = new Set([0, 1]);

function requireInteger(value, field, { min = 1, allowNull = false } = {}) {
  if (allowNull && (value === null || value === undefined)) return null;
  if (!Number.isInteger(value) || value < min) throw new TypeError(`Invalid ${field} value.`);
  return value;
}

function normalizeProviderId(value) {
  const numeric = typeof value === 'string' && /^\d+$/.test(value) ? Number(value) : value;
  if (!Number.isInteger(numeric) || numeric < 0 || numeric > 255) {
    throw new TypeError('Invalid two-factor provider identifier.');
  }
  return numeric;
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

export function normalizeTwoFactorChallenge(payload) {
  if (!payload || typeof payload !== 'object') throw new TypeError('Invalid authentication challenge.');
  if (payload.error !== 'invalid_grant' || payload.error_description !== 'Two factor required.') {
    throw new TypeError('Response is not a supported two-factor challenge.');
  }

  if (!Array.isArray(payload.TwoFactorProviders) || payload.TwoFactorProviders.length === 0) {
    throw new TypeError('Two-factor challenge has no providers.');
  }

  const providers = payload.TwoFactorProviders.map(normalizeProviderId);
  const sourceMetadata = payload.TwoFactorProviders2;
  if (sourceMetadata !== undefined && (sourceMetadata === null || typeof sourceMetadata !== 'object' || Array.isArray(sourceMetadata))) {
    throw new TypeError('Invalid two-factor provider metadata.');
  }

  const providerMetadata = {};
  for (const provider of providers) {
    const metadata = sourceMetadata?.[String(provider)] ?? null;
    if (metadata !== null && (typeof metadata !== 'object' || Array.isArray(metadata))) {
      throw new TypeError('Invalid two-factor provider metadata entry.');
    }
    providerMetadata[String(provider)] = metadata === null ? null : Object.freeze({ ...metadata });
  }

  return Object.freeze({
    kind: 'two-factor-required',
    providers: Object.freeze(providers),
    providerMetadata: Object.freeze(providerMetadata),
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
