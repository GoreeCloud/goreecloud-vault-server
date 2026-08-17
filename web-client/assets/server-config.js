import { requestApi } from './api-client.js';
import { runtimeConfig } from './runtime-config.js';

function requireString(value, field, maxLength = 512) {
  if (typeof value !== 'string' || !value || value.length > maxLength) throw new TypeError(`Invalid server ${field}.`);
  return value;
}

function requireOrigin(value, field) {
  const url = new URL(requireString(value, field));
  if (url.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(url.hostname)) {
    throw new TypeError(`Server ${field} must use HTTPS outside local development.`);
  }
  return url.origin + url.pathname.replace(/\/$/, '');
}

export function normalizeServerConfig(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new TypeError('Invalid GoreeVault server config.');
  if (payload.object !== 'config') throw new TypeError('Response is not a GoreeVault server config.');
  if (!payload.server || payload.server.name !== 'GoreeVault') throw new TypeError('Unexpected server identity.');
  if (!payload.environment || typeof payload.environment !== 'object') throw new TypeError('Server environment metadata is required.');

  const vault = requireOrigin(payload.environment.vault, 'vault origin');
  const api = requireOrigin(payload.environment.api, 'API origin');
  const identity = requireOrigin(payload.environment.identity, 'identity origin');
  const notifications = requireOrigin(payload.environment.notifications, 'notifications origin');

  if (vault !== runtimeConfig.productionOrigin && !vault.startsWith('http://localhost') && !vault.startsWith('http://127.0.0.1')) {
    throw new TypeError('Unexpected GoreeVault vault origin.');
  }

  return Object.freeze({
    name: 'GoreeVault',
    version: requireString(payload.version, 'version', 64),
    vault,
    api,
    identity,
    notifications,
    suppressOnboardingInterstitials: payload.settings?.suppressOnboardingInterstitials === true,
  });
}

export async function requestServerConfig(options = {}) {
  const response = await requestApi('/api/config', { ...options, method: 'GET' });
  return normalizeServerConfig(response.payload);
}
