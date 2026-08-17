import test from 'node:test';
import assert from 'node:assert/strict';

import { requestApi } from '../assets/api-client.js';

test('API requests enforce no-store, redirect rejection, and same-origin credential scope', async () => {
  let capturedUrl;
  let capturedOptions;
  const fetchImpl = async (url, options) => {
    capturedUrl = url;
    capturedOptions = options;
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  };

  const result = await requestApi('/api/accounts/prelogin', {
    method: 'POST',
    body: { email: 'user@example.com' },
    locationOrigin: 'http://localhost:8080',
    fetchImpl,
  });

  assert.equal(capturedUrl.origin, 'http://localhost:8080');
  assert.equal(capturedOptions.credentials, 'same-origin');
  assert.equal(capturedOptions.cache, 'no-store');
  assert.equal(capturedOptions.redirect, 'error');
  assert.equal(capturedOptions.referrerPolicy, 'same-origin');
  assert.equal(capturedOptions.headers.get('content-type'), 'application/json');
  assert.deepEqual(result.payload, { ok: true });
});

test('unapproved browser origins fail closed to the production GoreeVault origin', async () => {
  let capturedUrl;
  const fetchImpl = async (url) => {
    capturedUrl = url;
    return new Response(null, { status: 204 });
  };

  await requestApi('/api/config', {
    locationOrigin: 'https://unexpected.example',
    fetchImpl,
  });

  assert.equal(capturedUrl.origin, 'https://vault.goreecloud.com');
});

test('unsupported methods and timeouts are rejected before network use', async () => {
  let called = false;
  const fetchImpl = async () => {
    called = true;
    return new Response(null, { status: 204 });
  };

  await assert.rejects(() => requestApi('/api/config', { method: 'TRACE', fetchImpl }), /unsupported/i);
  await assert.rejects(() => requestApi('/api/config', { timeoutMs: 10, fetchImpl }), /timeout/i);
  assert.equal(called, false);
});
