import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const root = new URL('../', import.meta.url);

async function source(path) {
  return readFile(new URL(path, root), 'utf8');
}

test('Glaze sign-in preparation exposes email-only prelogin controls', async () => {
  const html = await source('index.html');
  assert.match(html, /id="prelogin-form"/);
  assert.match(html, /id="account-email"[^>]*type="email"/);
  assert.match(html, /id="prelogin-submit"/);
  assert.match(html, /No password entry/);
  assert.doesNotMatch(html, /type="password"/i);
  assert.doesNotMatch(html, /name="password"/i);
});

test('prelogin UI wiring stops after KDF metadata and keeps credential processing disabled', async () => {
  const app = await source('assets/app.js');
  const config = await source('assets/runtime-config.js');
  assert.match(app, /requestPreloginMetadata/);
  assert.match(app, /acceptPrelogin/);
  assert.match(app, /Password entry and cryptographic unlock remain disabled/);
  assert.doesNotMatch(app, /buildSecretBearingPasswordGrant/);
  assert.match(config, /credentialProcessingEnabled: false/);
});

test('unfinished vault navigation is explicitly disabled and cannot become the active view', async () => {
  const html = await source('index.html');
  const app = await source('assets/app.js');

  for (const route of ['favorites', 'organizations', 'send']) {
    assert.match(
      html,
      new RegExp(`href="#${route}"[^>]*aria-disabled="true"[^>]*data-prealpha-disabled="true"`),
    );
  }

  assert.match(app, /PREALPHA_DISABLED_ROUTES/);
  assert.match(app, /event\.preventDefault\(\)/);
  assert.match(app, /history\.replaceState\(null, '', '#vault'\)/);
  assert.match(html, /id="navigation-status"/);
});
