import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import test from 'node:test';

import {
  argon2idBrowserRuntimeBoundary,
  assertArgon2idBrowserProductionRegistrationDisabled,
  createValidationOnlyBrowserArgon2idProvider,
  validateArgon2idBrowserWasmUrl,
} from '../validation/argon2id-browser-runtime.js';

const expectedOrigin = 'https://vault.example.test';
const wasmUrl = '/assets/goreevault_web_argon2id_core_bg.wasm';
const metadata = Object.freeze({
  kdf: 1,
  kdfIterations: 4,
  kdfMemory: 32,
  kdfParallelism: 2,
});
const expectedOutput = new Uint8Array(32).fill(0x5a);

function createBindings({ initError = null, deriveError = null } = {}) {
  const calls = { init: [], derive: [] };
  return {
    calls,
    bindings: {
      async default(url) {
        calls.init.push(url);
        if (initError) throw initError;
      },
      async derive_argon2id_wasm(secret, salt, iterations, memoryKiB, parallelism) {
        calls.derive.push({
          secret: new Uint8Array(secret),
          salt: new Uint8Array(salt),
          iterations,
          memoryKiB,
          parallelism,
        });
        if (deriveError) throw deriveError;
        return new Uint8Array(expectedOutput);
      },
    },
  };
}

test('browser runtime boundary remains validation-only and unapproved', () => {
  assert.equal(argon2idBrowserRuntimeBoundary.productionRegistrationApproved, false);
  assert.equal(argon2idBrowserRuntimeBoundary.credentialProcessingApproved, false);
  assert.equal(argon2idBrowserRuntimeBoundary.automaticRegistration, false);
  assert.equal(argon2idBrowserRuntimeBoundary.productionBundleIncluded, false);
  assert.equal(argon2idBrowserRuntimeBoundary.thirdPartyOriginsAllowed, false);
  assert.equal(argon2idBrowserRuntimeBoundary.mutableWasmUrlsAllowed, false);
  assert.equal(assertArgon2idBrowserProductionRegistrationDisabled(), true);
});

test('browser WASM URL must be immutable, HTTPS, and same-origin', () => {
  assert.equal(
    validateArgon2idBrowserWasmUrl(wasmUrl, { expectedOrigin }),
    'https://vault.example.test/assets/goreevault_web_argon2id_core_bg.wasm',
  );

  assert.throws(
    () => validateArgon2idBrowserWasmUrl('https://cdn.example.test/core.wasm', { expectedOrigin }),
    /exact GoreeVault browser origin/,
  );
  assert.throws(
    () => validateArgon2idBrowserWasmUrl('/assets/core.wasm?v=2', { expectedOrigin }),
    /query/,
  );
  assert.throws(
    () => validateArgon2idBrowserWasmUrl('/assets/core.js', { expectedOrigin }),
    /\.wasm artifact/,
  );
  assert.throws(
    () => validateArgon2idBrowserWasmUrl('/assets/core.wasm', { expectedOrigin: 'http://vault.example.test' }),
    /must use HTTPS/,
  );
});

test('browser loader initializes exact same-origin WASM and returns an explicit provider', async () => {
  const { bindings, calls } = createBindings();
  const provider = await createValidationOnlyBrowserArgon2idProvider({
    loadBindings: async () => bindings,
    wasmUrl,
    expectedOrigin,
    implementationId: 'goreevault-browser-runtime-ci',
    evidenceReference: 'github-actions://browser-runtime-registration',
    subtle: webcrypto.subtle,
  });

  assert.deepEqual(calls.init, [
    'https://vault.example.test/assets/goreevault_web_argon2id_core_bg.wasm',
  ]);
  assert.equal(provider.algorithm, 'argon2id');
  assert.equal(provider.implementationId, 'goreevault-browser-runtime-ci');

  const result = await provider.deriveMasterKey({
    password: 'correct horse battery staple',
    accountIdentifier: 'User@Example.Test ',
    kdfMetadata: metadata,
  });
  try {
    assert.deepEqual(result, expectedOutput);
    assert.equal(calls.derive.length, 1);
    assert.equal(calls.derive[0].iterations, 4);
    assert.equal(calls.derive[0].memoryKiB, 32 * 1024);
    assert.equal(calls.derive[0].parallelism, 2);
    assert.equal(calls.derive[0].salt.length, 32);
  } finally {
    result.fill(0);
    calls.derive[0].secret.fill(0);
    calls.derive[0].salt.fill(0);
  }
});

test('browser loader fails closed on missing exports and initialization failure', async () => {
  await assert.rejects(
    createValidationOnlyBrowserArgon2idProvider({
      loadBindings: async () => ({ default: async () => {} }),
      wasmUrl,
      expectedOrigin,
      evidenceReference: 'ci://missing-export',
    }),
    /derive_argon2id_wasm/,
  );

  const expectedError = new Error('CSP blocked WebAssembly initialization');
  const { bindings } = createBindings({ initError: expectedError });
  await assert.rejects(
    createValidationOnlyBrowserArgon2idProvider({
      loadBindings: async () => bindings,
      wasmUrl,
      expectedOrigin,
      evidenceReference: 'ci://init-failure',
    }),
    expectedError,
  );
});

test('browser loader never performs automatic provider registration', async () => {
  const { bindings } = createBindings();
  const provider = await createValidationOnlyBrowserArgon2idProvider({
    loadBindings: async () => bindings,
    wasmUrl,
    expectedOrigin,
    evidenceReference: 'ci://manual-provider-handoff',
  });

  assert.equal(typeof provider.deriveMasterKey, 'function');
  assert.equal(argon2idBrowserRuntimeBoundary.automaticRegistration, false);
});
