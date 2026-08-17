import { decryptType2EncString } from './enc-string.js';

const USER_KEY_LENGTH = 64;

function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(`${label} is required.`);
  }
  return value;
}

function requireString(value, label) {
  if (typeof value !== 'string' || value.length === 0) throw new TypeError(`${label} is required.`);
  return value;
}

function normalizeKdf(value) {
  const kdf = requireObject(value, 'Master-password KDF metadata');
  if (!Number.isInteger(kdf.kdfType) || !Number.isInteger(kdf.iterations)) {
    throw new TypeError('Master-password KDF type and iterations are required.');
  }
  if (kdf.memory != null && !Number.isInteger(kdf.memory)) {
    throw new TypeError('Master-password KDF memory must be an integer when present.');
  }
  if (kdf.parallelism != null && !Number.isInteger(kdf.parallelism)) {
    throw new TypeError('Master-password KDF parallelism must be an integer when present.');
  }
  return Object.freeze({
    kdfType: kdf.kdfType,
    iterations: kdf.iterations,
    memory: kdf.memory ?? null,
    parallelism: kdf.parallelism ?? null,
  });
}

export function parseMasterPasswordUnlock(userDecryption) {
  const decryption = requireObject(userDecryption, 'User-decryption metadata');
  const unlock = requireObject(decryption.masterPasswordUnlock, 'Master-password unlock metadata');
  const wrappedUserKey = unlock.masterKeyWrappedUserKey ?? unlock.masterKeyEncryptedUserKey;

  return Object.freeze({
    kdf: normalizeKdf(unlock.kdf),
    salt: requireString(unlock.salt, 'Master-password unlock salt').trim().toLowerCase(),
    wrappedUserKey: requireString(wrappedUserKey, 'Master-key wrapped user key'),
  });
}

export function splitCompositeUserKey(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.length !== USER_KEY_LENGTH) {
    throw new TypeError('Decrypted user key must be exactly 64 bytes.');
  }
  return Object.freeze({
    encKey: bytes.slice(0, 32),
    macKey: bytes.slice(32, 64),
    algorithm: 'AES-256-CBC-HMAC-SHA256',
  });
}

export async function unwrapCompositeUserKey(unlock, stretchedMasterKey, options = {}) {
  const normalized = requireObject(unlock, 'Master-password unlock metadata');
  const decrypt = options.decryptType2EncString ?? decryptType2EncString;
  if (typeof decrypt !== 'function') throw new TypeError('A type-2 decryptor is required.');

  const plaintext = await decrypt(
    requireString(normalized.wrappedUserKey, 'Master-key wrapped user key'),
    stretchedMasterKey,
    options,
  );
  try {
    return splitCompositeUserKey(plaintext);
  } finally {
    if (plaintext instanceof Uint8Array) plaintext.fill(0);
  }
}

export function clearCompositeUserKey(userKey) {
  if (!userKey || typeof userKey !== 'object') return;
  if (userKey.encKey instanceof Uint8Array) userKey.encKey.fill(0);
  if (userKey.macKey instanceof Uint8Array) userKey.macKey.fill(0);
}
