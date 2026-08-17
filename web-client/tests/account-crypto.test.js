import assert from 'node:assert/strict';
import test from 'node:test';

import {
  clearCompositeUserKey,
  parseMasterPasswordUnlock,
  splitCompositeUserKey,
  unwrapCompositeUserKey,
} from '../assets/account-crypto.js';

test('sync master-password unlock metadata accepts current wrapped-user-key field', () => {
  const parsed = parseMasterPasswordUnlock({
    masterPasswordUnlock: {
      kdf: { kdfType: 0, iterations: 600000, memory: null, parallelism: null },
      masterKeyWrappedUserKey: '2.iv|cipher|mac',
      salt: 'User@Example.COM',
    },
  });
  assert.deepEqual(parsed.kdf, { kdfType: 0, iterations: 600000, memory: null, parallelism: null });
  assert.equal(parsed.salt, 'user@example.com');
  assert.equal(parsed.wrappedUserKey, '2.iv|cipher|mac');
});

test('sync master-password unlock metadata accepts legacy encrypted-user-key alias', () => {
  const parsed = parseMasterPasswordUnlock({
    masterPasswordUnlock: {
      kdf: { kdfType: 1, iterations: 3, memory: 64, parallelism: 4 },
      masterKeyEncryptedUserKey: 'legacy-alias',
      salt: 'user@example.com',
    },
  });
  assert.equal(parsed.wrappedUserKey, 'legacy-alias');
  assert.equal(parsed.kdf.kdfType, 1);
});

test('composite user key is exactly 64 bytes split into encryption and MAC halves', () => {
  const bytes = new Uint8Array(Array.from({ length: 64 }, (_, index) => index));
  const key = splitCompositeUserKey(bytes);
  assert.deepEqual([...key.encKey], [...bytes.slice(0, 32)]);
  assert.deepEqual([...key.macKey], [...bytes.slice(32)]);
  assert.throws(() => splitCompositeUserKey(new Uint8Array(32)), /exactly 64 bytes/);
});

test('user-key unwrap delegates to type-2 decryptor and clears plaintext buffer', async () => {
  const plaintext = new Uint8Array(Array.from({ length: 64 }, (_, index) => index + 1));
  let calledWith = null;
  const userKey = await unwrapCompositeUserKey(
    { wrappedUserKey: '2.test|value|mac' },
    { encKey: new Uint8Array(32), macKey: new Uint8Array(32) },
    {
      decryptType2EncString: async (value) => {
        calledWith = value;
        return plaintext;
      },
    },
  );

  assert.equal(calledWith, '2.test|value|mac');
  assert.equal(userKey.encKey.length, 32);
  assert.equal(userKey.macKey.length, 32);
  assert.ok(plaintext.every((value) => value === 0));
});

test('composite user key clearing zeroes both halves', () => {
  const key = splitCompositeUserKey(new Uint8Array(64).fill(7));
  clearCompositeUserKey(key);
  assert.ok(key.encKey.every((value) => value === 0));
  assert.ok(key.macKey.every((value) => value === 0));
});
