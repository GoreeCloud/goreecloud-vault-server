import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';

import {
  derivePasswordAuthenticationMaterial,
  deriveServerAuthorizationHash,
} from '../../../assets/auth-kdf.js';
import { createValidationOnlyWasmArgon2idProvider } from '../../../validation/argon2id-wasm-adapter.js';

const modulePath = process.argv[2];
if (!modulePath) throw new Error('Expected generated wasm-bindgen Node.js module path.');

const require = createRequire(import.meta.url);
const wasmModule = require(resolve(modulePath));
const password = 'asdfasdf';
const accountIdentifier = 'test@bitwarden.com';
const kdfMetadata = Object.freeze({
  kdf: 1,
  kdfIterations: 4,
  kdfMemory: 32,
  kdfParallelism: 2,
});
const normalizedEmailSha256 = new Uint8Array([
  150, 76, 72, 244, 143, 81, 217, 127, 203, 220, 24, 133, 13, 122, 88, 106,
  61, 85, 225, 171, 26, 32, 139, 77, 61, 116, 143, 113, 37, 10, 211, 63,
]);
const secret = new TextEncoder().encode(password);
let directOutput;
let providerOutput;

try {
  directOutput = wasmModule.derive_argon2id_wasm(secret, normalizedEmailSha256, 4, 32 * 1024, 2);
  assert.ok(directOutput instanceof Uint8Array);
  assert.equal(directOutput.length, 32);

  const provider = createValidationOnlyWasmArgon2idProvider({
    wasmModule,
    implementationId: 'goreevault-rustcrypto-argon2id-wasm-ci-validation',
    evidenceReference: 'github-actions://goreevault-web-argon2id-core/generated-bindings',
    subtle: webcrypto.subtle,
  });

  providerOutput = await provider.deriveMasterKey({
    password,
    accountIdentifier,
    kdfMetadata,
  });

  assert.deepEqual(providerOutput, directOutput);
  assert.notEqual(providerOutput.buffer, directOutput.buffer);

  const expectedPasswordHash = await deriveServerAuthorizationHash(directOutput, password, {
    subtle: webcrypto.subtle,
  });
  const authenticationMaterial = await derivePasswordAuthenticationMaterial({
    password,
    accountIdentifier,
    kdfMetadata,
  }, {
    argon2idProvider: provider,
    subtle: webcrypto.subtle,
  });

  assert.deepEqual(authenticationMaterial, {
    passwordHash: expectedPasswordHash,
    kdf: 'argon2id',
  });
  console.log('GoreeVault validation-only Argon2id WASM runtime adapter passed generated binding and authentication-material equivalence checks.');
} finally {
  secret.fill(0);
  normalizedEmailSha256.fill(0);
  if (directOutput instanceof Uint8Array) directOutput.fill(0);
  if (providerOutput instanceof Uint8Array) providerOutput.fill(0);
}
