import { normalizeAccountIdentifier } from './auth-protocol.js';

const ARGON2ID = 1;
const MASTER_KEY_BYTES = 32;
const ARGON2ID_VERSION = 0x13;
const ARGON2ID_MIN_MEMORY_MIB = 16;
const ARGON2ID_MIN_ITERATIONS = 2;
const ARGON2ID_MIN_PARALLELISM = 1;
const KIB_PER_MIB = 1024;
const U32_MAX = 0xFFFFFFFF;
const PROVIDER_BRAND = Symbol('GoreeVaultArgon2idProvider');
const encoder = new TextEncoder();

function requireU32AtLeast(value, minimum, field) {
  if (!Number.isInteger(value) || value < minimum || value > U32_MAX) {
    throw new TypeError(`Invalid ${field} value.`);
  }
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

function requireDigest(subtle = globalThis.crypto?.subtle) {
  if (!subtle || typeof subtle.digest !== 'function') {
    throw new Error('Web Crypto SHA-256 support is required for the Argon2id salt transform.');
  }
  return subtle;
}

async function sha256Bytes(bytes, subtle = globalThis.crypto?.subtle) {
  const digest = await requireDigest(subtle).digest('SHA-256', bytes);
  return new Uint8Array(digest);
}

export const argon2idProviderBoundary = Object.freeze({
  algorithm: 'argon2id',
  version: ARGON2ID_VERSION,
  builtInImplementationAvailable: false,
  fallbackAllowed: false,
  outputBytes: MASTER_KEY_BYTES,
  minimumIterations: ARGON2ID_MIN_ITERATIONS,
  minimumMemoryMiB: ARGON2ID_MIN_MEMORY_MIB,
  minimumParallelism: ARGON2ID_MIN_PARALLELISM,
  serverMemoryUnit: 'MiB',
  providerMemoryUnit: 'KiB',
  saltTransform: 'SHA-256(normalized-account-identifier)',
  secretStorage: 'memory-only',
  credentialProcessingEnabledByRegistration: false,
  approvalRequirement: 'Reviewed local implementation plus Bitwarden interoperability evidence.',
});

export function normalizeArgon2idMetadata(metadata) {
  if (!metadata || typeof metadata !== 'object') throw new TypeError('KDF metadata is required.');
  if (metadata.kdf !== ARGON2ID) throw new TypeError('Argon2id KDF metadata is required.');

  const iterations = requireU32AtLeast(metadata.kdfIterations, ARGON2ID_MIN_ITERATIONS, 'kdfIterations');
  const memoryMiB = requireU32AtLeast(metadata.kdfMemory, ARGON2ID_MIN_MEMORY_MIB, 'kdfMemory');
  const parallelism = requireU32AtLeast(metadata.kdfParallelism, ARGON2ID_MIN_PARALLELISM, 'kdfParallelism');
  const memoryKiB = memoryMiB * KIB_PER_MIB;
  if (!Number.isSafeInteger(memoryKiB) || memoryKiB > U32_MAX) {
    throw new TypeError('Invalid kdfMemory value.');
  }

  return Object.freeze({
    type: 'argon2id',
    version: ARGON2ID_VERSION,
    iterations,
    memoryMiB,
    memoryKiB,
    parallelism,
    outputBytes: MASTER_KEY_BYTES,
  });
}

export async function deriveArgon2idSalt(accountIdentifier, { subtle } = {}) {
  const normalizedAccount = normalizeAccountIdentifier(accountIdentifier);
  const saltInputBytes = encoder.encode(normalizedAccount);
  try {
    return await sha256Bytes(saltInputBytes, subtle);
  } finally {
    saltInputBytes.fill(0);
  }
}

export function createArgon2idProvider({ implementationId, evidenceReference, deriveKey, subtle } = {}) {
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
      const params = normalizeArgon2idMetadata(kdfMetadata);
      const secretBytes = encoder.encode(normalizedPassword);
      let saltBytes = null;

      try {
        saltBytes = await deriveArgon2idSalt(accountIdentifier, { subtle });
        const derived = await deriveKey(Object.freeze({
          algorithm: 'argon2id',
          version: params.version,
          secretBytes,
          saltBytes,
          iterations: params.iterations,
          memoryKiB: params.memoryKiB,
          parallelism: params.parallelism,
          outputBytes: params.outputBytes,
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
        if (saltBytes instanceof Uint8Array) saltBytes.fill(0);
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
