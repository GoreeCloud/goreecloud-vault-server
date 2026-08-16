import { normalizeAccountIdentifier } from './auth-protocol.js';
import { normalizeArgon2idMetadata, requireArgon2idProvider } from './argon2id-provider.js';

const PBKDF2 = 0;
const ARGON2ID = 1;
const PBKDF2_MIN_ITERATIONS = 5000;
const MASTER_KEY_BITS = 256;
const SERVER_AUTHORIZATION_PURPOSE = 1;
const encoder = new TextEncoder();

function requireSubtle(subtle = globalThis.crypto?.subtle) {
  if (!subtle || typeof subtle.importKey !== 'function' || typeof subtle.deriveBits !== 'function') {
    throw new Error('Web Crypto PBKDF2 support is required.');
  }
  return subtle;
}

function requirePassword(password) {
  if (typeof password !== 'string' || password.length === 0) {
    throw new TypeError('Master password must be a non-empty string.');
  }
  return password;
}

function requireSalt(salt) {
  if (typeof salt !== 'string' || salt.length === 0) throw new TypeError('KDF salt must be a non-empty string.');
  return salt;
}

function requirePbkdf2Iterations(iterations) {
  if (!Number.isInteger(iterations) || iterations < PBKDF2_MIN_ITERATIONS) {
    throw new RangeError(`PBKDF2 iterations must be at least ${PBKDF2_MIN_ITERATIONS}.`);
  }
  return iterations;
}

async function pbkdf2Sha256(secretBytes, saltBytes, iterations, subtle) {
  const key = await subtle.importKey('raw', secretBytes, 'PBKDF2', false, ['deriveBits']);
  const bits = await subtle.deriveBits({
    name: 'PBKDF2',
    hash: 'SHA-256',
    salt: saltBytes,
    iterations,
  }, key, MASTER_KEY_BITS);
  return new Uint8Array(bits);
}

export function bytesToBase64(bytes) {
  if (!(bytes instanceof Uint8Array)) throw new TypeError('Expected Uint8Array.');
  let binary = '';
  for (let index = 0; index < bytes.length; index += 1) binary += String.fromCharCode(bytes[index]);
  return btoa(binary);
}

export function assertSupportedKdf(metadata, { argon2idProvider } = {}) {
  if (!metadata || typeof metadata !== 'object') throw new TypeError('KDF metadata is required.');
  if (metadata.kdf === PBKDF2) {
    requirePbkdf2Iterations(metadata.kdfIterations);
    return Object.freeze({ type: 'pbkdf2', iterations: metadata.kdfIterations });
  }
  if (metadata.kdf === ARGON2ID) {
    const params = normalizeArgon2idMetadata(metadata);
    return Object.freeze({
      ...params,
      provider: requireArgon2idProvider(argon2idProvider),
    });
  }
  throw new Error('Unsupported GoreeVault KDF type.');
}

export async function derivePbkdf2KeyMaterial(secret, salt, iterations, { subtle } = {}) {
  const normalizedSecret = requirePassword(secret);
  const normalizedSalt = requireSalt(salt);
  const rounds = requirePbkdf2Iterations(iterations);
  return pbkdf2Sha256(
    encoder.encode(normalizedSecret),
    encoder.encode(normalizedSalt),
    rounds,
    requireSubtle(subtle),
  );
}

export async function deriveMasterKeyPbkdf2(password, accountIdentifier, iterations, options = {}) {
  return derivePbkdf2KeyMaterial(
    requirePassword(password),
    normalizeAccountIdentifier(accountIdentifier),
    iterations,
    options,
  );
}

export async function deriveServerAuthorizationHash(masterKey, password, { subtle } = {}) {
  if (!(masterKey instanceof Uint8Array) || masterKey.length !== 32) {
    throw new TypeError('Master key must be exactly 32 bytes.');
  }
  const normalizedPassword = requirePassword(password);
  const cryptoSubtle = requireSubtle(subtle);
  const hash = await pbkdf2Sha256(
    masterKey,
    encoder.encode(normalizedPassword),
    SERVER_AUTHORIZATION_PURPOSE,
    cryptoSubtle,
  );
  return bytesToBase64(hash);
}

export async function derivePasswordAuthenticationMaterial({ password, accountIdentifier, kdfMetadata } = {}, options = {}) {
  const supported = assertSupportedKdf(kdfMetadata, options);
  let masterKey;
  let kdf;

  if (supported.type === 'pbkdf2') {
    masterKey = await deriveMasterKeyPbkdf2(password, accountIdentifier, supported.iterations, options);
    kdf = 'pbkdf2-sha256';
  } else if (supported.type === 'argon2id') {
    masterKey = await supported.provider.deriveMasterKey({ password, accountIdentifier, kdfMetadata });
    kdf = 'argon2id';
  } else {
    throw new Error('Unsupported authentication KDF.');
  }

  try {
    const passwordHash = await deriveServerAuthorizationHash(masterKey, password, options);
    return Object.freeze({ passwordHash, kdf });
  } finally {
    masterKey.fill(0);
  }
}
