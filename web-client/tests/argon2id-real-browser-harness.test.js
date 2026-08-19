import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const runner = await readFile(new URL('../validation/argon2id-real-browser/runner.js', import.meta.url), 'utf8');
const page = await readFile(new URL('../validation/argon2id-real-browser/index.html', import.meta.url), 'utf8');

test('harness is fail-closed and never grants release approval', () => {
  assert.match(runner, /location\.protocol === 'https:'/);
  assert.match(runner, /moduleUrl\.origin === location\.origin/);
  assert.match(runner, /credentialProcessingApproved: false/);
  assert.match(runner, /productionReleaseApproved: false/);
  assert.match(runner, /stablePromotionApproved: false/);
  assert.match(runner, /providerRegistrationWasExplicit: false/);
  assert.match(runner, /accepted: false/);
});

test('harness uses only synthetic reviewed interoperability material', () => {
  assert.match(runner, /67t9b5g67\$%Dh89n/);
  assert.doesNotMatch(runner, /password\s*=\s*document/i);
  assert.match(page, /Do not enter a real master password or production account data/);
});

test('harness constrains network execution with CSP and same-origin artifacts', () => {
  assert.match(page, /default-src 'none'/);
  assert.match(page, /connect-src 'self'/);
  assert.match(page, /script-src 'self'/);
  assert.match(runner, /credentials: 'omit'/);
  assert.match(runner, /securitypolicyviolation/);
});

test('harness records artifact identity, performance, and memory observations', () => {
  assert.match(runner, /candidateManifestSha256/);
  assert.match(runner, /javascriptSha256/);
  assert.match(runner, /wasmSha256/);
  assert.match(runner, /deriveMsP50/);
  assert.match(runner, /deriveMsP95/);
  assert.match(runner, /deriveMsMax/);
  assert.match(runner, /measureUserAgentSpecificMemory/);
  assert.match(runner, /leakSuspected: false/);
});
