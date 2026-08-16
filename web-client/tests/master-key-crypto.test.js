import assert from 'node:assert/strict';
import test from 'node:test';

import { clearStretchedMasterKey, stretchMasterKey } from '../assets/master-key-crypto.js';

const masterKey = new Uint8Array([
  31, 79, 104, 226, 150, 71, 177, 90, 194, 80, 172, 209, 17, 129, 132, 81,
  138, 167, 69, 167, 254, 149, 2, 27, 39, 197, 64, 42, 22, 195, 86, 75,
]);

const expectedEncKey = new Uint8Array([
  111, 31, 178, 45, 238, 152, 37, 114, 143, 215, 124, 83, 135, 173, 195, 23,
  142, 134, 120, 249, 61, 132, 163, 182, 113, 197, 189, 204, 188, 21, 237, 96,
]);

const expectedMacKey = new Uint8Array([
  221, 127, 206, 234, 101, 27, 202, 38, 86, 52, 34, 28, 78, 28, 185, 16,
  48, 61, 127, 166, 209, 247, 194, 87, 232, 26, 48, 85, 193, 249, 179, 155,
]);

test('master-key stretching matches the Bitwarden SDK HKDF-Expand vector', async () => {
  const stretched = await stretchMasterKey(masterKey);
  assert.deepEqual(stretched.encKey, expectedEncKey);
  assert.deepEqual(stretched.macKey, expectedMacKey);
  assert.equal(stretched.algorithm, 'HKDF-Expand-SHA256');
});

test('stretched master-key material can be explicitly zeroed', async () => {
  const stretched = await stretchMasterKey(masterKey);
  clearStretchedMasterKey(stretched);
  assert.deepEqual(stretched.encKey, new Uint8Array(32));
  assert.deepEqual(stretched.macKey, new Uint8Array(32));
});

test('master-key stretching rejects invalid key length', async () => {
  await assert.rejects(() => stretchMasterKey(new Uint8Array(31)), /exactly 32 bytes/);
});
