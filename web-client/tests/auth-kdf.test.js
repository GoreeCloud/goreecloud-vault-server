import assert from 'node:assert/strict';
import test from 'node:test';

import {
  assertSupportedKdf,
  deriveMasterKeyPbkdf2,
  derivePasswordAuthenticationMaterial,
  derivePbkdf2KeyMaterial,
  deriveServerAuthorizationHash,
} from '../assets/auth-kdf.js';

const authoritativeMasterKeyVector = new Uint8Array([
  31, 79, 104, 226, 150, 71, 177, 90, 194, 80, 172, 209, 17, 129, 132, 81,
  138, 167, 69, 167, 254, 149, 2, 27, 39, 197, 64, 42, 22, 195, 86, 75,
]);

test('PBKDF2 master-key derivation matches the Bitwarden SDK vector', async () => {
  const actual = await derivePbkdf2KeyMaterial('67t9b5g67$%Dh89n', 'test_key', 10000);
  assert.deepEqual(actual, authoritativeMasterKeyVector);
});

test('account identifier normalization matches the Bitwarden SDK password-hash vector', async () => {
  for (const email of ['test@bitwarden.com', 'TEST@bitwarden.com', ' test@bitwarden.com']) {
    const masterKey = await deriveMasterKeyPbkdf2('asdfasdf', email, 100000);
    const passwordHash = await deriveServerAuthorizationHash(masterKey, 'asdfasdf');
    masterKey.fill(0);
    assert.equal(passwordHash, 'wmyadRMyBZOH7P/a/ucTCbSghKgdzDpPqUnu/DAVtSw=');
  }
});

test('production account derivation rejects non-email identifiers', async () => {
  await assert.rejects(
    () => deriveMasterKeyPbkdf2('asdfasdf', 'test_key', 100000),
    /valid account email identifier/,
  );
});

test('authentication material returns only the server authorization hash', async () => {
  const result = await derivePasswordAuthenticationMaterial({
    password: 'asdfasdf',
    accountIdentifier: 'test@bitwarden.com',
    kdfMetadata: { kdf: 0, kdfIterations: 100000, kdfMemory: null, kdfParallelism: null },
  });
  assert.deepEqual(result, {
    passwordHash: 'wmyadRMyBZOH7P/a/ucTCbSghKgdzDpPqUnu/DAVtSw=',
    kdf: 'pbkdf2-sha256',
  });
});

test('PBKDF2 rejects parameters below the Bitwarden SDK minimum', () => {
  assert.throws(
    () => assertSupportedKdf({ kdf: 0, kdfIterations: 4999 }),
    /at least 5000/,
  );
});

test('Argon2id remains fail-closed until a reviewed local implementation is available', () => {
  assert.throws(
    () => assertSupportedKdf({ kdf: 1, kdfIterations: 4, kdfMemory: 32, kdfParallelism: 2 }),
    /Argon2id authentication remains unavailable/,
  );
});
