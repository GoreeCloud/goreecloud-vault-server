import { createArgon2idProvider } from '../assets/argon2id-provider.js';

const DERIVE_EXPORT = 'derive_argon2id_wasm';
const OUTPUT_BYTES = 32;

export const argon2idWasmRuntimeBoundary = Object.freeze({
  purpose: 'validation-only-browser-runtime-adapter',
  wasmExport: DERIVE_EXPORT,
  productionRegistrationApproved: false,
  credentialProcessingApproved: false,
  automaticRegistration: false,
  outputBytes: OUTPUT_BYTES,
  secretCopiesCleared: true,
  wasmOutputCopyClearedWhenControllable: true,
});

function requireWasmModule(wasmModule) {
  if (!wasmModule || typeof wasmModule !== 'object') {
    throw new TypeError('A generated GoreeVault Argon2id WebAssembly module is required.');
  }
  if (typeof wasmModule[DERIVE_EXPORT] !== 'function') {
    throw new TypeError(`The WebAssembly module must export ${DERIVE_EXPORT}.`);
  }
  return wasmModule;
}

function requireProviderMetadata(value, field) {
  if (typeof value !== 'string' || value.trim().length === 0) {
    throw new TypeError(`${field} must be a non-empty string.`);
  }
  return value.trim();
}

function requireBytes(value, field, expectedLength = null) {
  if (!(value instanceof Uint8Array)) throw new TypeError(`${field} must be a Uint8Array.`);
  if (expectedLength !== null && value.length !== expectedLength) {
    throw new TypeError(`${field} must be exactly ${expectedLength} bytes.`);
  }
  return value;
}

function clear(bytes) {
  if (bytes instanceof Uint8Array) bytes.fill(0);
}

export function createValidationOnlyWasmArgon2idProvider({
  wasmModule,
  implementationId = 'goreevault-rustcrypto-argon2id-wasm-validation',
  evidenceReference,
  subtle,
} = {}) {
  const wasm = requireWasmModule(wasmModule);
  const id = requireProviderMetadata(implementationId, 'Argon2id implementation identifier');
  const evidence = requireProviderMetadata(evidenceReference, 'Argon2id evidence reference');

  return createArgon2idProvider({
    implementationId: id,
    evidenceReference: evidence,
    subtle,
    async deriveKey({ secretBytes, saltBytes, iterations, memoryKiB, parallelism, outputBytes }) {
      requireBytes(secretBytes, 'Argon2id secret bytes');
      requireBytes(saltBytes, 'Argon2id salt bytes', OUTPUT_BYTES);
      if (outputBytes !== OUTPUT_BYTES) throw new TypeError(`Argon2id output must be exactly ${OUTPUT_BYTES} bytes.`);

      const secretCopy = new Uint8Array(secretBytes);
      const saltCopy = new Uint8Array(saltBytes);
      let wasmOutput = null;

      try {
        wasmOutput = await wasm[DERIVE_EXPORT](secretCopy, saltCopy, iterations, memoryKiB, parallelism);
        requireBytes(wasmOutput, 'Argon2id WebAssembly output', OUTPUT_BYTES);

        const result = new Uint8Array(wasmOutput);
        if (result.buffer === wasmOutput.buffer) {
          clear(result);
          throw new Error('Argon2id WebAssembly output copy must use independent memory.');
        }
        return result;
      } finally {
        clear(secretCopy);
        clear(saltCopy);
        clear(wasmOutput);
      }
    },
  });
}

export function assertArgon2idWasmProductionRegistrationDisabled() {
  if (argon2idWasmRuntimeBoundary.productionRegistrationApproved !== false
    || argon2idWasmRuntimeBoundary.credentialProcessingApproved !== false
    || argon2idWasmRuntimeBoundary.automaticRegistration !== false) {
    throw new Error('Argon2id WebAssembly production registration must remain disabled.');
  }
  return true;
}
