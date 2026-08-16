import { normalizeAccountIdentifier } from './auth-protocol.js';

const ARGON2ID = 1;
const MASTER_KEY_BYTES = 32;
const PROVIDER_BRAND = Symbol('GoreeVaultArgon2idProvider');
const encoder = new TextEncoder();

function requirePositiveInteger(value, field) {
  if (!Number.isInteger(value) || value < 1) throw new TypeError(`Invalid ${field} value.`);
  return value;
}

function requireNonEmptyString(value, field) {
  if (typeof value !== 'string' || value.trim().length === 0) {
    throw new TypeError(`${field} must be a non-empty string.`);
  }
  return value.trim();
}

function requirePassword(password) {
  if (typeof password !== 'string' || password.length === 0) {
    throw new TypeError('Master password must be a non-empty string.');
  }
  return password;
}

export const argon2idProviderBoundary = Object.freeze({
  algorithm: 'argon2id',
  builtInImplementationAvailable: false,
  fallbackAllowed: false,
  outputBytes: MASTER_KEY_BYTES,
  secretStorage: 'memory-only',
  credentialProcessingEnabledByRegistration: false,
  approvalRequirement: 'Reviewed local implementation plus Bitwarden interoperability evidence.',
});

export function normalizeArgon2idMetadata(metadata) {
  if (!metadata || typeof metadata !== 'object') throw new TypeError('KDF metadata is required.');
  if (metadata.kdf !== ARGON2ID) throw new TypeError('Argon2id KDF metadata is required.');

  return Object.freeze({
    type: 'argon2id',
    iterations: requirePositiveInteger(metadata.kdfIterations, 'kdfIterations'),
    memory: requirePositiveInteger(metadata.kdfMemory, 'kdfMemory'),
    parallelism: requirePositiveInteger(metadata.kdfParallelism, 'kdfParallelism'),
  });
}

export function createArgon2idProvider({ implementationId, evidenceReference, deriveKey } = {}) {
  const id = requireNonEmptyString(implementationId, 'Argon2id implementation identifier');
  const evidence = requireNonEmptyString(evidenceReference, 'Argon2id evidence reference');
  if (typeof deriveKey !== 'function') throw new TypeError('Argon2id deriveKey must be a function.');

  const provider = {
    [PROVIDER_BRAND]: true,
    algorithm: 'argon2id',
    implementationId: id,
    evidenceReference: evidence,

    async deriveMasterKey({ password, accountIdentifier, kdfMetadata } = {}) {
      const normalizedPassword = requirePassword(password);
      const normalizedAccount = normalizeAccountIdentifier(accountIdentifier);
      const params = normalizeArgon2idMetadata(kdfMetadata);
      const secretBytes = encoder.encode(normalizedPassword);
      const saltBytes = encoder.encode(normalizedAccount);

      try {
        const derived = await deriveKey(Object.freeze({
          secretBytes,
          saltBytes,
          iterations: params.iterations,
          memory: params.memory,
          parallelism: params.parallelism,
          outputBytes: MASTER_KEY_BYTES,
        }));

        if (!(derived instanceof Uint8Array) || derived.length !== MASTER_KEY_BYTES) {
          if (derived instanceof Uint8Array) derived.fill(0);
          throw new TypeError(`Argon2id provider must return exactly ${MASTER_KEY_BYTES} bytes.`);
        }
        if (derived.buffer === secretBytes.buffer || derived.buffer === saltBytes.buffer) {
          derived.fill(0);
          throw new Error('Argon2id provider output must use an independent buffer.');
        }
        return derived;
      } finally {
        secretBytes.fill(0);
        saltBytes.fill(0);
      }
    },
  };

  return Object.freeze(provider);
}

export function requireArgon2idProvider(provider) {
  if (!provider || provider[PROVIDER_BRAND] !== true || provider.algorithm !== 'argon2id') {
    throw new Error(
      'Argon2id authentication remains unavailable until a reviewed local provider is explicitly registered.',
    );
  }
  return provider;
}
