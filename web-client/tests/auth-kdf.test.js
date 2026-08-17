import assert from 'node:assert/strict';
import test from 'node:test';

import {
  assertSupportedKdf,
  deriveMasterKeyPbkdf2,
  derivePasswordAuthenticationMaterial,
  derivePbkdf2KeyMaterial,
  deriveServerAuthorizationHash,
} from '../assets/auth-kdf.js';
import {
  argon2idProviderBoundary,
  createArgon2idProvider,
  deriveArgon2idSalt,
  normalizeArgon2idMetadata,
} from '../assets/argon2id-provider.js';

const authoritativeMasterKeyVector = new Uint8Array([
  31, 79, 104, 226, 150, 71, 177, 90, 194, 80, 172, 209, 17, 129, 132, 81,
  138, 167, 69, 167, 254, 149, 2, 27, 39, 197, 64, 42, 22, 195, 86, 75,
]);
const normalizedEmailSha256 = new Uint8Array([
  150, 76, 72, 244, 143, 81, 217, 127, 203, 220, 24, 133, 13, 122, 88, 106,
  61, 85, 225, 171, 26, 32, 139, 77, 61, 116, 143, 113, 37, 10, 211, 63,
]);
const argon2idMetadata = Object.freeze({
  kdf: 1,
  kdfIterations: 4,
  kdfMemory: 32,
  kdfParallelism: 2,
});

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

test('Argon2id remains fail-closed when no provider is explicitly registered', () => {
  assert.equal(argon2idProviderBoundary.builtInImplementationAvailable, false);
  assert.equal(argon2idProviderBoundary.fallbackAllowed, false);
  assert.equal(argon2idProviderBoundary.version, 0x13);
  assert.equal(argon2idProviderBoundary.minimumIterations, 2);
  assert.equal(argon2idProviderBoundary.minimumMemoryMiB, 16);
  assert.equal(argon2idProviderBoundary.minimumParallelism, 1);
  assert.equal(argon2idProviderBoundary.saltTransform, 'SHA-256(normalized-account-identifier)');
  assert.throws(
    () => assertSupportedKdf(argon2idMetadata),
    /reviewed local provider is explicitly registered/,
  );
});

test('Argon2id metadata mirrors Bitwarden minimums and converts MiB to KiB', () => {
  assert.deepEqual(normalizeArgon2idMetadata(argon2idMetadata), {
    type: 'argon2id',
    version: 0x13,
    iterations: 4,
    memoryMiB: 32,
    memoryKiB: 32768,
    parallelism: 2,
    outputBytes: 32,
  });
  assert.throws(
    () => normalizeArgon2idMetadata({ ...argon2idMetadata, kdfIterations: 1 }),
    /Invalid kdfIterations value/,
  );
  assert.throws(
    () => normalizeArgon2idMetadata({ ...argon2idMetadata, kdfMemory: 15 }),
    /Invalid kdfMemory value/,
  );
  assert.throws(
    () => normalizeArgon2idMetadata({ ...argon2idMetadata, kdfParallelism: 0 }),
    /Invalid kdfParallelism value/,
  );
});

test('Argon2id salt is SHA-256 of the normalized account identifier', async () => {
  const salt = await deriveArgon2idSalt(' TEST@bitwarden.com ');
  assert.deepEqual(salt, normalizedEmailSha256);
  salt.fill(0);
});

test('registered Argon2id provider receives Bitwarden-compatible parameters and cleared memory-only inputs', async () => {
  const masterKeyVector = Uint8Array.from({ length: 32 }, (_, index) => index + 1);
  const expectedMasterKey = new Uint8Array(masterKeyVector);
  const expectedHash = await deriveServerAuthorizationHash(expectedMasterKey, 'asdfasdf');
  expectedMasterKey.fill(0);

  let retainedSecret;
  let retainedSalt;
  let retainedMasterKey;
  let observedSecret;
  let observedSalt;
  let observedParams;
  const provider = createArgon2idProvider({
    implementationId: 'test-only-provider',
    evidenceReference: 'test-only interoperability seam',
    deriveKey: async (request) => {
      retainedSecret = request.secretBytes;
      retainedSalt = request.saltBytes;
      observedSecret = new Uint8Array(request.secretBytes);
      observedSalt = new Uint8Array(request.saltBytes);
      observedParams = {
        algorithm: request.algorithm,
        version: request.version,
        iterations: request.iterations,
        memoryKiB: request.memoryKiB,
        parallelism: request.parallelism,
        outputBytes: request.outputBytes,
      };
      retainedMasterKey = new Uint8Array(masterKeyVector);
      return retainedMasterKey;
    },
  });

  const result = await derivePasswordAuthenticationMaterial({
    password: 'asdfasdf',
    accountIdentifier: ' TEST@bitwarden.com ',
    kdfMetadata: argon2idMetadata,
  }, { argon2idProvider: provider });

  assert.deepEqual(result, { passwordHash: expectedHash, kdf: 'argon2id' });
  assert.equal(new TextDecoder().decode(observedSecret), 'asdfasdf');
  assert.deepEqual(observedSalt, normalizedEmailSha256);
  assert.deepEqual(observedParams, {
    algorithm: 'argon2id',
    version: 0x13,
    iterations: 4,
    memoryKiB: 32768,
    parallelism: 2,
    outputBytes: 32,
  });
  assert.deepEqual(retainedSecret, new Uint8Array('asdfasdf'.length));
  assert.deepEqual(retainedSalt, new Uint8Array(32));
  assert.deepEqual(retainedMasterKey, new Uint8Array(32));
});

test('Argon2id provider output must be an independent 32-byte buffer', async () => {
  let shortOutput;
  const shortProvider = createArgon2idProvider({
    implementationId: 'test-short-provider',
    evidenceReference: 'negative test',
    deriveKey: async () => {
      shortOutput = new Uint8Array(31).fill(7);
      return shortOutput;
    },
  });

  await assert.rejects(
    () => derivePasswordAuthenticationMaterial({
      password: 'asdfasdf',
      accountIdentifier: 'test@bitwarden.com',
      kdfMetadata: argon2idMetadata,
    }, { argon2idProvider: shortProvider }),
    /exactly 32 bytes/,
  );
  assert.deepEqual(shortOutput, new Uint8Array(31));

  const aliasedProvider = createArgon2idProvider({
    implementationId: 'test-aliased-provider',
    evidenceReference: 'negative test',
    deriveKey: async ({ secretBytes }) => secretBytes,
  });
  await assert.rejects(
    () => derivePasswordAuthenticationMaterial({
      password: 'a'.repeat(32),
      accountIdentifier: 'test@bitwarden.com',
      kdfMetadata: argon2idMetadata,
    }, { argon2idProvider: aliasedProvider }),
    /independent buffer/,
  );
});

test('Argon2id provider errors propagate without PBKDF2 fallback', async () => {
  const provider = createArgon2idProvider({
    implementationId: 'test-failing-provider',
    evidenceReference: 'negative test',
    deriveKey: async () => {
      throw new Error('argon-provider-failure');
    },
  });

  await assert.rejects(
    () => derivePasswordAuthenticationMaterial({
      password: 'asdfasdf',
      accountIdentifier: 'test@bitwarden.com',
      kdfMetadata: argon2idMetadata,
    }, { argon2idProvider: provider }),
    /argon-provider-failure/,
  );
});
