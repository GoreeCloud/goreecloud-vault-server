import test from 'node:test';
import assert from 'node:assert/strict';

import { normalizeServerConfig } from '../assets/server-config.js';

function fixture() {
  return {
    object: 'config',
    version: '2026.6.0',
    server: { name: 'GoreeVault', url: 'https://github.com/GoreeCloud/goreevault-server' },
    settings: { suppressOnboardingInterstitials: true },
    environment: {
      vault: 'https://vault.goreecloud.com',
      api: 'https://vault.goreecloud.com/api',
      identity: 'https://vault.goreecloud.com/identity',
      notifications: 'https://vault.goreecloud.com/notifications',
    },
  };
}

test('server config accepts the canonical GoreeVault environment', () => {
  const config = normalizeServerConfig(fixture());
  assert.equal(config.name, 'GoreeVault');
  assert.equal(config.version, '2026.6.0');
  assert.equal(config.vault, 'https://vault.goreecloud.com');
  assert.equal(config.identity, 'https://vault.goreecloud.com/identity');
  assert.equal(config.suppressOnboardingInterstitials, true);
});

test('server config rejects unexpected identity and production origins', () => {
  const wrongIdentity = fixture();
  wrongIdentity.server.name = 'Other';
  assert.throws(() => normalizeServerConfig(wrongIdentity), /server identity/i);

  const wrongOrigin = fixture();
  wrongOrigin.environment.vault = 'https://example.com';
  assert.throws(() => normalizeServerConfig(wrongOrigin), /unexpected goreevault vault origin/i);
});
