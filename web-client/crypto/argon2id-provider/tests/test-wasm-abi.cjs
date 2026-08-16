'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');

const modulePath = process.argv[2];
if (!modulePath) {
  throw new Error('Usage: node test-wasm-abi.cjs <generated-module.js>');
}

const bindings = require(path.resolve(modulePath));
assert.equal(typeof bindings.derive_argon2id_wasm, 'function');

const secret = new TextEncoder().encode('67t9b5g67$%Dh89n');
const salt = Uint8Array.from([
  146, 72, 142, 30, 62, 238, 205, 249, 159, 62, 210, 206, 89, 35, 62, 251,
  75, 79, 182, 18, 213, 101, 92, 12, 233, 234, 82, 181, 165, 2, 230, 85,
]);
const expected = Uint8Array.from([
  207, 240, 225, 177, 162, 19, 163, 76, 98, 106, 179, 175, 224, 9, 17, 240,
  20, 147, 237, 47, 246, 150, 141, 184, 62, 225, 131, 242, 51, 53, 225, 242,
]);

const derived = bindings.derive_argon2id_wasm(secret, salt, 4, 32 * 1024, 2);
assert.ok(derived instanceof Uint8Array);
assert.deepEqual(derived, expected, 'WASM ABI must reproduce the reviewed Bitwarden vector');
assert.notEqual(derived.buffer, secret.buffer);
assert.notEqual(derived.buffer, salt.buffer);

assert.throws(
  () => bindings.derive_argon2id_wasm(secret, new Uint8Array(31), 4, 32 * 1024, 2),
  /invalid-salt-length/,
);
assert.throws(
  () => bindings.derive_argon2id_wasm(secret, salt, 1, 32 * 1024, 2),
  /insufficient-parameters/,
);

console.log('GoreeVault Argon2id WASM ABI interoperability validation passed.');
