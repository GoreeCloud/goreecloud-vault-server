const encoder = new TextEncoder();
const SHA256_LENGTH = 32;

function requireSubtle(subtle = globalThis.crypto?.subtle) {
  if (!subtle || typeof subtle.importKey !== 'function' || typeof subtle.sign !== 'function') {
    throw new Error('Web Crypto HMAC-SHA256 support is required.');
  }
  return subtle;
}

function requireMasterKey(masterKey) {
  if (!(masterKey instanceof Uint8Array) || masterKey.length !== SHA256_LENGTH) {
    throw new TypeError('Master key must be exactly 32 bytes.');
  }
  return masterKey;
}

async function hmacSha256(keyBytes, dataBytes, subtle) {
  const key = await subtle.importKey(
    'raw',
    keyBytes,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  return new Uint8Array(await subtle.sign('HMAC', key, dataBytes));
}

export async function hkdfExpandSha256(prk, info, { subtle } = {}) {
  const keyMaterial = requireMasterKey(prk);
  if (typeof info !== 'string') throw new TypeError('HKDF info must be a string.');
  const cryptoSubtle = requireSubtle(subtle);

  // Bitwarden stretches to one SHA-256 block (32 bytes), so HKDF-Expand is T(1) only:
  // HMAC(PRK, info || 0x01). No HKDF-Extract step is performed here.
  const infoBytes = encoder.encode(info);
  const input = new Uint8Array(infoBytes.length + 1);
  input.set(infoBytes, 0);
  input[input.length - 1] = 1;
  return hmacSha256(keyMaterial, input, cryptoSubtle);
}

export async function stretchMasterKey(masterKey, options = {}) {
  requireMasterKey(masterKey);
  const [encKey, macKey] = await Promise.all([
    hkdfExpandSha256(masterKey, 'enc', options),
    hkdfExpandSha256(masterKey, 'mac', options),
  ]);
  return Object.freeze({ encKey, macKey, algorithm: 'HKDF-Expand-SHA256' });
}

export function clearStretchedMasterKey(stretched) {
  if (!stretched || typeof stretched !== 'object') return;
  if (stretched.encKey instanceof Uint8Array) stretched.encKey.fill(0);
  if (stretched.macKey instanceof Uint8Array) stretched.macKey.fill(0);
}
