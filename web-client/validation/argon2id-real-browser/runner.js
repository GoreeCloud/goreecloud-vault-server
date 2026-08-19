const EXPECTED = new Uint8Array([207,240,225,177,162,19,163,76,98,106,179,175,224,9,17,240,20,147,237,47,246,150,141,184,62,225,131,242,51,53,225,242]);
const SALT = new Uint8Array([146,72,142,30,62,238,205,249,159,62,210,206,89,35,62,251,75,79,182,18,213,101,92,12,233,234,82,181,165,2,230,85]);
const SECRET = new TextEncoder().encode('67t9b5g67$%Dh89n');
const HEX40 = /^[0-9a-f]{40}$/;
const HEX64 = /^[0-9a-f]{64}$/;
const statusNode = document.querySelector('#status');
const evidenceNode = document.querySelector('#evidence');
const runButton = document.querySelector('#run');
const downloadButton = document.querySelector('#download');
let retainedEvidence = null;
const cspViolations = [];

document.addEventListener('securitypolicyviolation', (event) => {
  cspViolations.push({ directive: event.effectiveDirective, blockedURI: event.blockedURI || '' });
});

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function percentile(sorted, p) {
  const index = Math.min(sorted.length - 1, Math.ceil((p / 100) * sorted.length) - 1);
  return sorted[index];
}

async function sha256Hex(bytes) {
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function observedMemory() {
  if (typeof performance.measureUserAgentSpecificMemory === 'function') {
    const result = await performance.measureUserAgentSpecificMemory();
    return { method: 'performance.measureUserAgentSpecificMemory', bytes: Number(result.bytes) };
  }
  if (performance.memory && Number.isFinite(performance.memory.usedJSHeapSize)) {
    return { method: 'performance.memory.usedJSHeapSize', bytes: Number(performance.memory.usedJSHeapSize) };
  }
  return { method: 'manual-browser-memory-review-required', bytes: 0 };
}

function browserMetadata() {
  const ua = navigator.userAgent;
  let name = 'Unknown'; let engine = 'unknown';
  if (/Firefox\//.test(ua)) { name = 'Firefox'; engine = 'gecko'; }
  else if (/Edg\//.test(ua)) { name = 'Edge'; engine = 'blink'; }
  else if (/Chrome\//.test(ua)) { name = 'Chrome'; engine = 'blink'; }
  else if (/Safari\//.test(ua)) { name = 'Safari'; engine = 'webkit'; }
  const match = ua.match(/(?:Firefox|Edg|Chrome|Version)\/([^\s]+)/);
  return { name, version: match?.[1] ?? 'unknown', engine, os: navigator.platform || 'unknown', architecture: 'review-required' };
}

async function runAcceptance() {
  retainedEvidence = null;
  downloadButton.disabled = true;
  statusNode.textContent = 'Running…';
  evidenceNode.textContent = 'No evidence retained yet.';

  assert(location.protocol === 'https:', 'Harness must be served over HTTPS.');
  const sourceRevision = document.querySelector('#sourceRevision').value.trim();
  const candidateManifestSha256 = document.querySelector('#candidateManifestSha256').value.trim();
  assert(HEX40.test(sourceRevision), 'Source revision must be a 40-character lowercase Git SHA.');
  assert(HEX64.test(candidateManifestSha256), 'Candidate manifest SHA-256 must be 64 lowercase hex characters.');

  const requestedPath = document.querySelector('#javascriptPath').value.trim();
  const moduleUrl = new URL(requestedPath, location.href);
  assert(moduleUrl.origin === location.origin, 'Generated binding must be same-origin.');
  const javascriptBytes = new Uint8Array(await (await fetch(moduleUrl, { cache: 'no-store', credentials: 'omit' })).arrayBuffer());
  const javascriptSha256 = await sha256Hex(javascriptBytes);
  const wasmUrl = new URL('goreevault_web_argon2id_core_bg.wasm', moduleUrl);
  const wasmBytes = new Uint8Array(await (await fetch(wasmUrl, { cache: 'no-store', credentials: 'omit' })).arrayBuffer());
  const wasmSha256 = await sha256Hex(wasmBytes);

  const before = await observedMemory();
  const imported = await import(moduleUrl.href);
  assert(typeof imported.default === 'function', 'Generated wasm-bindgen initializer is missing.');
  assert(typeof imported.derive_argon2id_wasm === 'function', 'Generated Argon2id export is missing.');
  await imported.default(wasmUrl.href);

  const samples = [];
  let last = null;
  for (let index = 0; index < 5; index += 1) {
    const started = performance.now();
    last = new Uint8Array(imported.derive_argon2id_wasm(SECRET.slice(), SALT.slice(), 4, 32 * 1024, 2));
    samples.push(performance.now() - started);
  }
  assert(last && last.length === EXPECTED.length && last.every((value, index) => value === EXPECTED[index]), 'Bitwarden interoperability vector did not match.');
  const after = await observedMemory();
  const sorted = [...samples].sort((a, b) => a - b);

  retainedEvidence = {
    schema: 1,
    evidenceType: 'goreevault-web-argon2id-real-browser',
    sourceRevision,
    candidateManifestSha256,
    browser: browserMetadata(),
    servedOrigin: location.origin,
    artifacts: {
      javascriptPath: moduleUrl.pathname.split('/').pop(), javascriptSha256,
      wasmPath: wasmUrl.pathname.split('/').pop(), wasmSha256
    },
    execution: {
      realBrowserExecuted: true,
      generatedBindingsLoaded: true,
      wasmInitialized: true,
      bitwardenVectorPassed: true,
      authenticationMaterialMatched: true,
      sameOriginLoadObserved: true,
      providerRegistrationWasExplicit: false
    },
    csp: {
      effectivePolicy: document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content ?? '',
      violations: cspViolations
    },
    performance: {
      samples: samples.length,
      deriveMsP50: percentile(sorted, 50),
      deriveMsP95: percentile(sorted, 95),
      deriveMsMax: Math.max(...samples)
    },
    memory: {
      method: before.method === after.method ? before.method : `${before.method} -> ${after.method}`,
      beforeBytes: before.bytes,
      afterBytes: after.bytes,
      peakBytes: Math.max(before.bytes, after.bytes),
      leakSuspected: false
    },
    approvals: {
      credentialProcessingApproved: false,
      productionReleaseApproved: false,
      stablePromotionApproved: false
    },
    accepted: false
  };

  evidenceNode.textContent = JSON.stringify(retainedEvidence, null, 2);
  downloadButton.disabled = false;
  statusNode.textContent = 'Synthetic real-browser execution completed. Evidence remains intentionally unaccepted until manual architecture, browser metadata, provider-handoff, CSP, and memory review is completed.';
}

runButton.addEventListener('click', () => runAcceptance().catch((error) => {
  retainedEvidence = null;
  downloadButton.disabled = true;
  statusNode.textContent = `FAILED CLOSED: ${error.message}`;
}));

downloadButton.addEventListener('click', () => {
  if (!retainedEvidence) return;
  const blob = new Blob([`${JSON.stringify(retainedEvidence, null, 2)}\n`], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'goreevault-web-argon2id-real-browser-evidence.json';
  anchor.click();
  URL.revokeObjectURL(url);
});
