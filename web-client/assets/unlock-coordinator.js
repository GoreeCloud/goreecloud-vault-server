import { normalizeAccountIdentifier } from './auth-protocol.js';
import { assertSupportedKdf, derivePbkdf2KeyMaterial } from './auth-kdf.js';
import { clearStretchedMasterKey, stretchMasterKey } from './master-key-crypto.js';
import {
  clearCompositeUserKey,
  parseMasterPasswordUnlock,
  unwrapCompositeUserKey,
} from './account-crypto.js';

function requireOperation(operation) {
  if (typeof operation !== 'function') throw new TypeError('Unlocked-key operation must be a function.');
  return operation;
}

function kdfMetadata(unlock) {
  return {
    kdf: unlock.kdf.kdfType,
    kdfIterations: unlock.kdf.iterations,
    kdfMemory: unlock.kdf.memory,
    kdfParallelism: unlock.kdf.parallelism,
  };
}

export async function withMasterPasswordUserKey({
  password,
  accountIdentifier,
  userDecryption,
} = {}, operation, options = {}) {
  const run = requireOperation(operation);
  const normalizedAccount = normalizeAccountIdentifier(accountIdentifier);
  const unlock = parseMasterPasswordUnlock(userDecryption);

  if (unlock.salt !== normalizedAccount) {
    throw new Error('Master-password unlock salt does not match the selected account.');
  }

  const supported = assertSupportedKdf(kdfMetadata(unlock));
  if (supported.type !== 'pbkdf2') {
    throw new Error('Only reviewed PBKDF2 account unlock is available in this pre-alpha boundary.');
  }

  const derive = options.derivePbkdf2KeyMaterial ?? derivePbkdf2KeyMaterial;
  const stretch = options.stretchMasterKey ?? stretchMasterKey;
  const unwrap = options.unwrapCompositeUserKey ?? unwrapCompositeUserKey;
  if (typeof derive !== 'function' || typeof stretch !== 'function' || typeof unwrap !== 'function') {
    throw new TypeError('Unlock coordinator cryptographic operations must be functions.');
  }

  const masterKey = await derive(password, unlock.salt, supported.iterations, options);
  let stretched = null;
  let userKey = null;
  try {
    stretched = await stretch(masterKey, options);
    userKey = await unwrap(unlock, stretched, options);
    return await run(userKey, Object.freeze({
      accountIdentifier: normalizedAccount,
      kdf: supported.type,
    }));
  } finally {
    clearCompositeUserKey(userKey);
    clearStretchedMasterKey(stretched);
    if (masterKey instanceof Uint8Array) masterKey.fill(0);
  }
}

export const unlockCoordinatorBoundary = Object.freeze({
  mode: 'memory-only-scoped-callback',
  networkAccess: false,
  persistentKeyStorage: false,
  supportedKdf: 'pbkdf2-only-pre-alpha',
});
