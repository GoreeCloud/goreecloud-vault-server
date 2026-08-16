import assert from 'node:assert/strict';
import test from 'node:test';

import { decryptType2EncString, parseType2EncString } from '../assets/enc-string.js';

const serialized = '2.2NokAMS6llUxk26oueMqrA==|6k0QD71SJLy2WEBDkV4esiTrgkP/z7eoSedSesGLGYE=|PE4sb0jpAwZW+tnyPuW43eeWvSxjvdw3xMJlPGbDlYI=';
const key = new Uint8Array(Array.from({ length: 64 }, (_, index) => index));

test('type-2 EncString parser matches Bitwarden serialized ordering', () => {
  const parsed = parseType2EncString(serialized);
  assert.equal(parsed.type, 2);
  assert.equal(parsed.iv.length, 16);
  assert.equal(parsed.ciphertext.length, 32);
  assert.equal(parsed.mac.length, 32);
});

test('serialized type-2 EncString decrypts the Bitwarden SDK vector', async () => {
  const plaintext = await decryptType2EncString(serialized, {
    encKey: key.slice(0, 32),
    macKey: key.slice(32),
  });
  assert.equal(new TextDecoder().decode(plaintext), 'Bitwarden SDK test vector');
});

test('type-2 parser rejects unauthenticated legacy type 0', () => {
  assert.throws(() => parseType2EncString('0.AA==|AA=='), /Only Bitwarden type-2/);
});

test('type-2 parser rejects malformed IV and MAC lengths', () => {
  assert.throws(() => parseType2EncString('2.AA==|AAAAAAAAAAAAAAAAAAAAAA==|AA=='), /IV must be exactly 16 bytes/);
});
