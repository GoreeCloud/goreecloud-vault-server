import { normalizeTwoFactorChallenge } from './auth-protocol.js';
import { runtimeConfig, buildApiUrl } from './runtime-config.js';

const TOKEN_PATH = '/identity/connect/token';
const TOKEN_TYPE = 'Bearer';
const encoder = new TextEncoder();

function requireString(value, field, maxLength = 16384) {
  if (typeof value !== 'string' || value.length === 0 || value.length > maxLength) {
    throw new TypeError(`Invalid ${field}.`);
  }
  return value;
}

function requirePositiveInteger(value, field) {
  if (!Number.isInteger(value) || value <= 0) throw new TypeError(`Invalid ${field}.`);
  return value;
}

export function encodeIdentityForm(fields) {
  if (!fields || typeof fields !== 'object' || Array.isArray(fields)) {
    throw new TypeError('Identity form fields are required.');
  }
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null) continue;
    if (typeof value !== 'string') throw new TypeError(`Identity field ${key} must be a string.`);
    params.set(key, value);
  }
  return params.toString();
}

export function normalizeIdentitySuccess(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new TypeError('Invalid identity token response.');
  }
  const accessToken = requireString(payload.access_token, 'access token');
  const refreshToken = requireString(payload.refresh_token, 'refresh token');
  const expiresIn = requirePositiveInteger(payload.expires_in, 'token lifetime');
  const tokenType = requireString(payload.token_type, 'token type', 64);
  const scope = requireString(payload.scope, 'token scope', 512);
  if (tokenType !== TOKEN_TYPE) throw new TypeError('Unsupported identity token type.');
  if (!scope.split(/\s+/).includes('api')) throw new TypeError('Identity token scope does not include api.');

  return Object.freeze({
    kind: 'authenticated',
    accessToken,
    refreshToken,
    expiresIn,
    tokenType,
    scope,
  });
}

export function normalizeIdentityResponse({ status, payload } = {}) {
  if (!Number.isInteger(status)) throw new TypeError('Identity response status is required.');
  if (status >= 200 && status < 300) return normalizeIdentitySuccess(payload);
  if (payload?.error === 'invalid_grant' && payload?.error_description === 'Two factor required.') {
    return normalizeTwoFactorChallenge(payload);
  }
  return Object.freeze({ kind: 'rejected', status, error: typeof payload?.error === 'string' ? payload.error : 'request_failed' });
}

export async function requestIdentityToken(fields, {
  signal,
  timeoutMs = 15000,
  locationOrigin = globalThis.window?.location?.origin ?? runtimeConfig.productionOrigin,
  fetchImpl = globalThis.fetch,
} = {}) {
  if (!runtimeConfig.credentialProcessingEnabled) {
    throw new Error('Identity token exchange is disabled until credential processing is approved.');
  }
  if (typeof fetchImpl !== 'function') throw new Error('Fetch implementation is required.');
  if (!Number.isFinite(timeoutMs) || timeoutMs < 1000 || timeoutMs > 60000) {
    throw new RangeError('Identity timeout must be between 1000 and 60000 milliseconds.');
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort('timeout'), timeoutMs);
  const abortExternal = () => controller.abort(signal?.reason ?? 'cancelled');
  if (signal) {
    if (signal.aborted) abortExternal();
    else signal.addEventListener('abort', abortExternal, { once: true });
  }

  try {
    const response = await fetchImpl(buildApiUrl(TOKEN_PATH, locationOrigin), {
      method: 'POST',
      headers: Object.freeze({
        Accept: 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
      }),
      body: encodeIdentityForm(fields),
      signal: controller.signal,
      credentials: 'same-origin',
      cache: 'no-store',
      redirect: 'error',
      referrerPolicy: 'same-origin',
    });
    let payload = null;
    const contentType = response.headers?.get?.('content-type') ?? '';
    if (contentType.includes('application/json')) {
      try { payload = await response.json(); } catch (_) { payload = null; }
    }
    return normalizeIdentityResponse({ status: response.status, payload });
  } finally {
    clearTimeout(timer);
    if (signal) signal.removeEventListener('abort', abortExternal);
  }
}

export const identityProtocol = Object.freeze({
  tokenPath: TOKEN_PATH,
  contentType: 'application/x-www-form-urlencoded',
  credentialProcessingEnabled: runtimeConfig.credentialProcessingEnabled,
  requestBytesEncoding: encoder.encoding,
});
