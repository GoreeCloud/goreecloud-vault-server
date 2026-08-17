import assert from 'node:assert/strict';
import test from 'node:test';

import {
  unlockCoordinatorBoundary,
  withMasterPasswordUserKey,
} from '../assets/unlock-coordinator.js';

function userDecryption(overrides = {}) {
  return {
    masterPasswordUnlock: {
      kdf: { kdfType: 0, iterations: 600000, memory: null, parallelism: null },
      salt: 'user@example.com',
      masterKeyWrappedUserKey: '2.placeholder|placeholder|placeholder',
      ...overrides,
    },
  };
}

test('unlock coordinator is explicitly memory-only and non-networked', () => {
  assert.equal(unlockCoordinatorBoundary.mode, 'memory-only-scoped-callback');
  assert.equal(unlockCoordinatorBoundary.networkAccess, false);
  assert.equal(unlockCoordinatorBoundary.persistentKeyStorage, false);
  assert.equal(unlockCoordinatorBoundary.supportedKdf, 'pbkdf2-only-pre-alpha');
});

test('scoped unlock composes derivation, stretching, unwrap, and clears all key buffers', async () => {
  const masterKey = new Uint8Array(32).fill(1);
  const stretched = {
    encKey: new Uint8Array(32).fill(2),
    macKey: new Uint8Array(32).fill(3),
  };
  const userKey = {
    encKey: new Uint8Array(32).fill(4),
    macKey: new Uint8Array(32).fill(5),
  };
  const calls = [];

  const result = await withMasterPasswordUserKey({
    password: 'correct horse battery staple',
    accountIdentifier: 'USER@EXAMPLE.COM',
    userDecryption: userDecryption(),
  }, async (key, context) => {
    calls.push('operation');
    assert.equal(context.accountIdentifier, 'user@example.com');
    assert.equal(context.kdf, 'pbkdf2');
    assert.equal(key.encKey[0], 4);
    assert.equal(key.macKey[0], 5);
    return 'done';
  }, {
    derivePbkdf2KeyMaterial: async (password, salt, iterations) => {
      calls.push('derive');
      assert.equal(password, 'correct horse battery staple');
      assert.equal(salt, 'user@example.com');
      assert.equal(iterations, 600000);
      return masterKey;
    },
    stretchMasterKey: async (key) => {
      calls.push('stretch');
      assert.equal(key, masterKey);
      return stretched;
    },
    unwrapCompositeUserKey: async (unlock, key) => {
      calls.push('unwrap');
      assert.equal(unlock.salt, 'user@example.com');
      assert.equal(key, stretched);
      return userKey;
    },
  });

  assert.equal(result, 'done');
  assert.deepEqual(calls, ['derive', 'stretch', 'unwrap', 'operation']);
  assert.ok(masterKey.every((byte) => byte === 0));
  assert.ok(stretched.encKey.every((byte) => byte === 0));
  assert.ok(stretched.macKey.every((byte) => byte === 0));
  assert.ok(userKey.encKey.every((byte) => byte === 0));
  assert.ok(userKey.macKey.every((byte) => byte === 0));
});

test('scoped unlock clears keys when the caller operation fails', async () => {
  const masterKey = new Uint8Array(32).fill(7);
  const stretched = {
    encKey: new Uint8Array(32).fill(8),
    macKey: new Uint8Array(32).fill(9),
  };
  const userKey = {
    encKey: new Uint8Array(32).fill(10),
    macKey: new Uint8Array(32).fill(11),
  };

  await assert.rejects(
    withMasterPasswordUserKey({
      password: 'password',
      accountIdentifier: 'user@example.com',
      userDecryption: userDecryption(),
    }, async () => {
      throw new Error('operation failed');
    }, {
      derivePbkdf2KeyMaterial: async () => masterKey,
      stretchMasterKey: async () => stretched,
      unwrapCompositeUserKey: async () => userKey,
    }),
    /operation failed/,
  );

  assert.ok(masterKey.every((byte) => byte === 0));
  assert.ok(stretched.encKey.every((byte) => byte === 0));
  assert.ok(stretched.macKey.every((byte) => byte === 0));
  assert.ok(userKey.encKey.every((byte) => byte === 0));
  assert.ok(userKey.macKey.every((byte) => byte === 0));
});

test('scoped unlock rejects account/salt mismatch before any cryptography runs', async () => {
  let derived = false;
  await assert.rejects(
    withMasterPasswordUserKey({
      password: 'password',
      accountIdentifier: 'other@example.com',
      userDecryption: userDecryption(),
    }, async () => undefined, {
      derivePbkdf2KeyMaterial: async () => {
        derived = true;
        return new Uint8Array(32);
      },
    }),
    /does not match the selected account/,
  );
  assert.equal(derived, false);
});

test('scoped unlock keeps Argon2id fail-closed', async () => {
  await assert.rejects(
    withMasterPasswordUserKey({
      password: 'password',
      accountIdentifier: 'user@example.com',
      userDecryption: userDecryption({
        kdf: { kdfType: 1, iterations: 3, memory: 64, parallelism: 4 },
      }),
    }, async () => undefined),
    /Argon2id authentication remains unavailable/,
  );
});
