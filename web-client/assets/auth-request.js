import { normalizeAccountIdentifier } from './auth-protocol.js';
import { runtimeConfig } from './runtime-config.js';

export const PASSWORD_GRANT = 'password';
export const PASSWORD_SCOPE = 'api offline_access';
export const WEB_CLIENT_ID = 'web';
export const UNKNOWN_BROWSER_DEVICE_TYPE = 14;

function requireNonEmptyString(value, field, maxLength = 256) {
  if (typeof value !== 'string') throw new TypeError(`${field} must be a string.`);
  const normalized = value.trim();
  if (!normalized || normalized.length > maxLength) throw new TypeError(`Invalid ${field}.`);
  return normalized;
}

export function createEphemeralBrowserDevice({
  identifier = globalThis.crypto?.randomUUID?.(),
  name = 'GoreeVault Web',
  type = UNKNOWN_BROWSER_DEVICE_TYPE,
} = {}) {
  const normalizedIdentifier = requireNonEmptyString(identifier, 'device identifier', 128);
  const normalizedName = requireNonEmptyString(name, 'device name', 64);
  if (!Number.isInteger(type) || type < 0 || type > 255) throw new TypeError('Invalid device type.');

  return Object.freeze({
    identifier: normalizedIdentifier,
    name: normalizedName,
    type,
    persistence: 'memory-only-pre-alpha',
  });
}

export function buildPasswordGrantEnvelope({ accountIdentifier, device } = {}) {
  if (!device || typeof device !== 'object') throw new TypeError('Device metadata is required.');

  return Object.freeze({
    grant_type: PASSWORD_GRANT,
    client_id: WEB_CLIENT_ID,
    scope: PASSWORD_SCOPE,
    username: normalizeAccountIdentifier(accountIdentifier),
    device_identifier: requireNonEmptyString(device.identifier, 'device identifier', 128),
    device_name: requireNonEmptyString(device.name, 'device name', 64),
    device_type: String(device.type),
  });
}

export function buildSecretBearingPasswordGrant({ accountIdentifier, device, passwordHash, twoFactor } = {}) {
  if (!runtimeConfig.credentialProcessingEnabled) {
    throw new Error('Secret-bearing password grants are disabled until credential processing is approved.');
  }

  const request = { ...buildPasswordGrantEnvelope({ accountIdentifier, device }) };
  request.password = requireNonEmptyString(passwordHash, 'password hash', 4096);

  if (twoFactor !== undefined) {
    if (!twoFactor || typeof twoFactor !== 'object') throw new TypeError('Invalid two-factor response.');
    if (!Number.isInteger(twoFactor.provider)) throw new TypeError('Invalid two-factor provider.');
    request.two_factor_provider = String(twoFactor.provider);
    request.two_factor_token = requireNonEmptyString(twoFactor.token, 'two-factor token', 4096);
    request.two_factor_remember = twoFactor.remember === true ? '1' : '0';
  }

  return Object.freeze(request);
}
