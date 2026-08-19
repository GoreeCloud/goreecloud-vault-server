import { createValidationOnlyWasmArgon2idProvider } from './argon2id-wasm-adapter.js';

const DERIVE_EXPORT = 'derive_argon2id_wasm';
const BROWSER_INIT_EXPORT = 'default';

export const argon2idBrowserRuntimeBoundary = Object.freeze({
  purpose: 'validation-only-browser-loader-and-registration-contract',
  productionRegistrationApproved: false,
  credentialProcessingApproved: false,
  automaticRegistration: false,
  productionBundleIncluded: false,
  thirdPartyOriginsAllowed: false,
  mutableWasmUrlsAllowed: false,
});

function requireNonEmptyString(value, field) {
  if (typeof value !== 'string' || value.trim().length === 0) {
    throw new TypeError(`${field} must be a non-empty string.`);
  }
  return value.trim();
}

function requireExpectedOrigin(expectedOrigin) {
  const origin = new URL(requireNonEmptyString(expectedOrigin, 'Expected browser origin'));
  if (origin.username || origin.password || origin.search || origin.hash) {
    throw new TypeError('Expected browser origin must not contain credentials, a query, or a fragment.');
  }
  if (origin.protocol !== 'https:') {
    throw new TypeError('Expected browser origin must use HTTPS.');
  }
  return origin.origin;
}

export function validateArgon2idBrowserWasmUrl(wasmUrl, { expectedOrigin } = {}) {
  const origin = requireExpectedOrigin(expectedOrigin);
  const url = new URL(requireNonEmptyString(wasmUrl, 'Argon2id WebAssembly URL'), `${origin}/`);

  if (url.origin !== origin) {
    throw new Error('Argon2id WebAssembly must load from the exact GoreeVault browser origin.');
  }
  if (url.protocol !== 'https:') {
    throw new Error('Argon2id WebAssembly must load over HTTPS.');
  }
  if (url.username || url.password || url.search || url.hash) {
    throw new Error('Argon2id WebAssembly URL must not contain credentials, a query, or a fragment.');
  }
  if (!url.pathname.endsWith('.wasm')) {
    throw new Error('Argon2id WebAssembly URL must identify a .wasm artifact.');
  }

  return url.href;
}

function requireBrowserBindings(bindings) {
  if (!bindings || typeof bindings !== 'object') {
    throw new TypeError('Generated GoreeVault browser bindings are required.');
  }
  if (typeof bindings[BROWSER_INIT_EXPORT] !== 'function') {
    throw new TypeError('Generated browser bindings must expose the wasm-bindgen default initializer.');
  }
  if (typeof bindings[DERIVE_EXPORT] !== 'function') {
    throw new TypeError(`Generated browser bindings must export ${DERIVE_EXPORT}.`);
  }
  return bindings;
}

export async function createValidationOnlyBrowserArgon2idProvider({
  loadBindings,
  wasmUrl,
  expectedOrigin,
  implementationId = 'goreevault-rustcrypto-argon2id-wasm-browser-validation',
  evidenceReference,
  subtle,
} = {}) {
  assertArgon2idBrowserProductionRegistrationDisabled();
  if (typeof loadBindings !== 'function') {
    throw new TypeError('A generated browser-binding loader function is required.');
  }

  const validatedWasmUrl = validateArgon2idBrowserWasmUrl(wasmUrl, { expectedOrigin });
  const bindings = requireBrowserBindings(await loadBindings());
  await bindings.default(validatedWasmUrl);

  return createValidationOnlyWasmArgon2idProvider({
    wasmModule: bindings,
    implementationId,
    evidenceReference,
    subtle,
  });
}

export function assertArgon2idBrowserProductionRegistrationDisabled() {
  if (argon2idBrowserRuntimeBoundary.productionRegistrationApproved !== false
    || argon2idBrowserRuntimeBoundary.credentialProcessingApproved !== false
    || argon2idBrowserRuntimeBoundary.automaticRegistration !== false
    || argon2idBrowserRuntimeBoundary.productionBundleIncluded !== false
    || argon2idBrowserRuntimeBoundary.thirdPartyOriginsAllowed !== false
    || argon2idBrowserRuntimeBoundary.mutableWasmUrlsAllowed !== false) {
    throw new Error('Argon2id browser production registration must remain disabled.');
  }
  return true;
}
