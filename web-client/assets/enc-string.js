import { decryptAes256CbcHmacSha256 } from './aes-cbc-hmac.js';

function decodeBase64(value, field) {
  if (typeof value !== 'string' || value.length === 0) throw new TypeError(`Invalid ${field}.`);
  let binary;
  try {
    binary = atob(value);
  } catch (_) {
    throw new TypeError(`Invalid ${field} base64.`);
  }
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

export function parseType2EncString(value) {
  if (typeof value !== 'string') throw new TypeError('Encrypted string must be a string.');
  const match = /^2\.([^|]+)\|([^|]+)\|([^|]+)$/.exec(value);
  if (!match) throw new TypeError('Only Bitwarden type-2 encrypted strings are supported by this boundary.');

  const iv = decodeBase64(match[1], 'IV');
  const ciphertext = decodeBase64(match[2], 'ciphertext');
  const mac = decodeBase64(match[3], 'MAC');
  if (iv.length !== 16) throw new TypeError('Type-2 IV must be exactly 16 bytes.');
  if (mac.length !== 32) throw new TypeError('Type-2 MAC must be exactly 32 bytes.');
  if (ciphertext.length === 0 || ciphertext.length % 16 !== 0) {
    throw new TypeError('Type-2 ciphertext must be a non-empty AES-CBC block sequence.');
  }
  return Object.freeze({ type: 2, iv, ciphertext, mac });
}

export async function decryptType2EncString(value, stretchedKey, options = {}) {
  if (!stretchedKey || !(stretchedKey.encKey instanceof Uint8Array) || !(stretchedKey.macKey instanceof Uint8Array)) {
    throw new TypeError('A stretched encryption/MAC key pair is required.');
  }
  const encrypted = parseType2EncString(value);
  return decryptAes256CbcHmacSha256({
    iv: encrypted.iv,
    ciphertext: encrypted.ciphertext,
    mac: encrypted.mac,
    encKey: stretchedKey.encKey,
    macKey: stretchedKey.macKey,
  }, options);
}
