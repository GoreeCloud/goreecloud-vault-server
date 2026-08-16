function requireSubtle(subtle = globalThis.crypto?.subtle) {
  if (!subtle || typeof subtle.importKey !== 'function' || typeof subtle.sign !== 'function' || typeof subtle.decrypt !== 'function') {
    throw new Error('Web Crypto AES-CBC and HMAC-SHA256 support is required.');
  }
  return subtle;
}

function requireBytes(value, length, field) {
  if (!(value instanceof Uint8Array) || (length !== null && value.length !== length)) {
    throw new TypeError(`${field} must be ${length === null ? 'a byte array' : `exactly ${length} bytes`}.`);
  }
  return value;
}

function constantTimeEqual(left, right) {
  if (!(left instanceof Uint8Array) || !(right instanceof Uint8Array) || left.length !== right.length) return false;
  let diff = 0;
  for (let index = 0; index < left.length; index += 1) diff |= left[index] ^ right[index];
  return diff === 0;
}

async function calculateMac(iv, ciphertext, macKey, subtle) {
  const hmacKey = await subtle.importKey(
    'raw',
    macKey,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const authenticated = new Uint8Array(iv.length + ciphertext.length);
  authenticated.set(iv, 0);
  authenticated.set(ciphertext, iv.length);
  return new Uint8Array(await subtle.sign('HMAC', hmacKey, authenticated));
}

export async function decryptAes256CbcHmacSha256({ iv, ciphertext, mac, encKey, macKey } = {}, { subtle } = {}) {
  requireBytes(iv, 16, 'IV');
  requireBytes(ciphertext, null, 'ciphertext');
  requireBytes(mac, 32, 'MAC');
  requireBytes(encKey, 32, 'encryption key');
  requireBytes(macKey, 32, 'MAC key');
  if (ciphertext.length === 0 || ciphertext.length % 16 !== 0) throw new TypeError('Ciphertext must be a non-empty AES-CBC block sequence.');

  const cryptoSubtle = requireSubtle(subtle);
  const expectedMac = await calculateMac(iv, ciphertext, macKey, cryptoSubtle);
  if (!constantTimeEqual(expectedMac, mac)) throw new Error('Encrypted value integrity check failed.');

  const aesKey = await cryptoSubtle.importKey('raw', encKey, { name: 'AES-CBC' }, false, ['decrypt']);
  try {
    return new Uint8Array(await cryptoSubtle.decrypt({ name: 'AES-CBC', iv }, aesKey, ciphertext));
  } catch (_) {
    throw new Error('Encrypted value decryption failed.');
  }
}
