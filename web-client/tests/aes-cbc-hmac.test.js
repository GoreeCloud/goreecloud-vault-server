import assert from 'node:assert/strict';
import test from 'node:test';

import { decryptAes256CbcHmacSha256 } from '../assets/aes-cbc-hmac.js';

const iv = new Uint8Array([
  216, 218, 36, 0, 196, 186, 150, 85, 49, 147, 110, 168, 185, 227, 42, 172,
]);
const mac = new Uint8Array([
  60, 78, 44, 111, 72, 233, 3, 6, 86, 250, 217, 242, 62, 229, 184, 221,
  231, 150, 189, 44, 99, 189, 220, 55, 196, 194, 101, 60, 102, 195, 149, 130,
]);
const ciphertext = new Uint8Array([
  234, 77, 16, 15, 189, 82, 36, 188, 182, 88, 64, 67, 145, 94, 30, 178,
  36, 235, 130, 67, 255, 207, 183, 168, 73, 231, 82, 122, 193, 139, 25, 129,
]);
const key = new Uint8Array(Array.from({ length: 64 }, (_, index) => index));

test('AES-256-CBC-HMAC-SHA256 decryption matches the Bitwarden SDK vector', async () => {
  const plaintext = await decryptAes256CbcHmacSha256({
    iv,
    ciphertext,
    mac,
    encKey: key.slice(0, 32),
    macKey: key.slice(32),
  });
  assert.equal(new TextDecoder().decode(plaintext), 'Bitwarden SDK test vector');
});

test('AES-256-CBC-HMAC-SHA256 rejects a modified MAC before decryption', async () => {
  const modified = mac.slice();
  modified[0] ^= 1;
  await assert.rejects(() => decryptAes256CbcHmacSha256({
    iv,
    ciphertext,
    mac: modified,
    encKey: key.slice(0, 32),
    macKey: key.slice(32),
  }), /integrity check failed/);
});

test('AES-256-CBC-HMAC-SHA256 rejects malformed block lengths', async () => {
  await assert.rejects(() => decryptAes256CbcHmacSha256({
    iv,
    ciphertext: new Uint8Array([1, 2, 3]),
    mac,
    encKey: key.slice(0, 32),
    macKey: key.slice(32),
  }), /block sequence/);
});
