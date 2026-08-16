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

test('unfinished vault navigation stays on vault and uses in-app Glaze feedback', async () => {
  const html = await source('index.html');
  const app = await source('assets/app.js');
  const feedback = await source('assets/feedback.css');

  for (const route of ['favorites', 'organizations', 'send']) {
    assert.match(
      html,
      new RegExp(`href="#${route}"[^>]*aria-disabled="true"[^>]*data-prealpha-disabled="true"`),
    );
  }

  assert.doesNotMatch(html, /title="(?:Favorites|Organizations|Send) is not available/);
  assert.match(html, /id="app-toast"[^>]*role="status"/);
  assert.match(html, /id="app-toast-dismiss"/);
  assert.match(app, /showToast/);
  assert.match(app, /TOAST_DURATION_MS/);
  assert.match(app, /event\.preventDefault\(\)/);
  assert.match(app, /history\.replaceState\(null, '', '#vault'\)/);
  assert.match(feedback, /\.app-toast/);
});

test('readiness copy distinguishes proven foundations from production approval', async () => {
  const html = await source('index.html');
  assert.match(html, /PBKDF2, token-state, and authenticated-sync foundations/);
  assert.match(html, /HKDF, AES-CBC-HMAC, and type-2 EncString primitives/);
  assert.match(html, /Argon2id and reviewed end-to-end vault crypto/);
  assert.match(html, /implemented, automated foundations—not authorization for production credentials/);
});
