function unavailable(operation) {
  throw new Error(`${operation} is unavailable until a reviewed compatible cryptography adapter is implemented.`);
}

export const cryptoBoundary = Object.freeze({
  implementation: 'unavailable-pre-alpha',
  deriveKeys() {
    return unavailable('Key derivation');
  },
  encryptVaultItem() {
    return unavailable('Vault encryption');
  },
  decryptVaultItem() {
    return unavailable('Vault decryption');
  },
  encryptAttachment() {
    return unavailable('Attachment encryption');
  },
  decryptAttachment() {
    return unavailable('Attachment decryption');
  },
  clearSensitiveState() {
    // The pre-alpha shell retains no derived key or decrypted vault material.
  },
});
