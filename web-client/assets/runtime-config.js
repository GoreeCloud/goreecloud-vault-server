const PRODUCTION_ORIGIN = 'https://vault.goreecloud.com';
const DEVELOPMENT_ORIGINS = new Set([
  'http://127.0.0.1:8080',
  'http://localhost:8080',
]);

function normalizeOrigin(value) {
  const url = new URL(value);
  return url.origin;
}

export function resolveServerOrigin(locationOrigin = window.location.origin) {
  const current = normalizeOrigin(locationOrigin);
  if (current === PRODUCTION_ORIGIN) return PRODUCTION_ORIGIN;
  if (DEVELOPMENT_ORIGINS.has(current)) return current;
  return PRODUCTION_ORIGIN;
}

export function buildApiUrl(path, locationOrigin = window.location.origin) {
  if (typeof path !== 'string' || !path.startsWith('/') || path.startsWith('//')) {
    throw new TypeError('API paths must be absolute application paths.');
  }
  const origin = resolveServerOrigin(locationOrigin);
  return new URL(path, `${origin}/`);
}

export const runtimeConfig = Object.freeze({
  productionOrigin: PRODUCTION_ORIGIN,
  telemetryEnabled: false,
  credentialProcessingEnabled: false,
  persistentDecryptedStateEnabled: false,
  offlinePrivateResponseCachingEnabled: false,
});
