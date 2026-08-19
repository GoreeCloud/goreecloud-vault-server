import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import test from 'node:test';

import {
  argon2idWasmRuntimeBoundary,
  assertArgon2idWasmProductionRegistrationDisabled,
  createValidationOnlyWasmArgon2idProvider,
} from '../validation/argon2id-wasm-adapter.js';

const metadata = Object.freeze({
  kdf: 1,
  kdfIterations: 4,
  kdfMemory: 32,
  kdfParallelism: 2,
});

const expected = new Uint8Array([
  207, 240, 225, 177, 162, 19, 163, 76, 98, 106, 179, 175, 224, 9, 17, 240,
  20, 147, 237, 47, 246, 150, 141, 184, 62, 225, 131, 242, 51, 53, 225, 242,
]);

function createStubWasm({ output = expected, error = null } = {}) {
  const calls = [];
  const wasmModule = {
    async derive_argon2id_wasm(secret, salt, iterations, memoryKiB, parallelism) {
      calls.push({ secret, salt, iterations, memoryKiB, parallelism });
      if (error) throw error;
      return new Uint8Array(output);
    },
  };
  return { wasmModule, calls };
}

test('runtime boundary remains validation-only and unapproved for credential processing', () => {
  assert.equal(argon2idWasmRuntimeBoundary.productionRegistrationApproved, false);
  assert.equal(argon2idWasmRuntimeBoundary.credentialProcessingApproved, false);
  assert.equal(argon2idWasmRuntimeBoundary.automaticRegistration, false);
  assert.equal(assertArgon2idWasmProductionRegistrationDisabled(), true);
});

test('adapter wraps the exact wasm-bindgen export and preserves Bitwarden-compatible parameters', async () => {
  const { wasmModule, calls } = createStubWasm();
  const provider = createValidationOnlyWasmArgon2idProvider({
    wasmModule,
    evidenceReference: 'ci://goreevault/argon2id-bindings/exact-head',
    subtle: webcrypto.subtle,
  });

  const result = await provider.deriveMasterKey({
    password: '67t9b5g67$%Dh89n',
    accountIdentifier: 'user@example.com',
    kdfMetadata: metadata,
  });

  assert.deepEqual(result, expected);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].iterations, 4);
  assert.equal(calls[0].memoryKiB, 32 * 1024);
  assert.equal(calls[0].parallelism, 2);
  assert.equal(calls[0].salt.length, 32);
  assert.ok(calls[0].secret.every((byte) => byte === 0), 'adapter-owned secret copy must be cleared');
  assert.ok(calls[0].salt.every((byte) => byte === 0), 'adapter-owned salt copy must be cleared');
});

test('adapter clears controlled wasm output after copying it to independent caller-owned memory', async () => {
  let returnedByWasm;
  const wasmModule = {
    derive_argon2id_wasm() {
      returnedByWasm = new Uint8Array(expected);
      return returnedByWasm;
    },
  };
  const provider = createValidationOnlyWasmArgon2idProvider({
    wasmModule,
    evidenceReference: 'ci://goreevault/argon2id-bindings/exact-head',
    subtle: webcrypto.subtle,
  });

  const result = await provider.deriveMasterKey({
    password: '67t9b5g67$%Dh89n',
    accountIdentifier: 'user@example.com',
    kdfMetadata: metadata,
  });

  assert.deepEqual(result, expected);
  assert.notEqual(result.buffer, returnedByWasm.buffer);
  assert.ok(returnedByWasm.every((byte) => byte === 0), 'controllable wasm output must be cleared');
  assert.ok(result.some((byte) => byte !== 0), 'returned independent result must remain intact');
});

test('missing or malformed wasm modules fail closed', () => {
  assert.throws(
    () => createValidationOnlyWasmArgon2idProvider({ evidenceReference: 'ci://evidence' }),
    /WebAssembly module is required/,
  );
  assert.throws(
    () => createValidationOnlyWasmArgon2idProvider({ wasmModule: {}, evidenceReference: 'ci://evidence' }),
    /derive_argon2id_wasm/,
  );
});

test('wasm failures propagate without fallback and adapter-owned copies are cleared', async () => {
  const { wasmModule, calls } = createStubWasm({ error: new Error('derivation-failed') });
  const provider = createValidationOnlyWasmArgon2idProvider({
    wasmModule,
    evidenceReference: 'ci://goreevault/argon2id-bindings/exact-head',
    subtle: webcrypto.subtle,
  });

  await assert.rejects(
    provider.deriveMasterKey({
      password: '67t9b5g67$%Dh89n',
      accountIdentifier: 'user@example.com',
      kdfMetadata: metadata,
    }),
    /derivation-failed/,
  );

  assert.equal(calls.length, 1);
  assert.ok(calls[0].secret.every((byte) => byte === 0));
  assert.ok(calls[0].salt.every((byte) => byte === 0));
});

test('malformed wasm output fails closed and is cleared when controllable', async () => {
  let malformed;
  const wasmModule = {
    derive_argon2id_wasm() {
      malformed = new Uint8Array(31).fill(7);
      return malformed;
    },
  };
  const provider = createValidationOnlyWasmArgon2idProvider({
    wasmModule,
    evidenceReference: 'ci://goreevault/argon2id-bindings/exact-head',
    subtle: webcrypto.subtle,
  });

  await assert.rejects(
    provider.deriveMasterKey({
      password: '67t9b5g67$%Dh89n',
      accountIdentifier: 'user@example.com',
      kdfMetadata: metadata,
    }),
    /exactly 32 bytes/,
  );
  assert.ok(malformed.every((byte) => byte === 0));
});
