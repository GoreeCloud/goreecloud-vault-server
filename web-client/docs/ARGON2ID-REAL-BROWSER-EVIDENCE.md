# GoreeVault Web Argon2id Real-Browser Evidence

## Purpose

This document defines the retained evidence required to prove that the GoreeVault Web Argon2id browser path was exercised in a real supported browser against exact generated browser artifacts.

The validator at `web-client/scripts/validate_browser_argon2id_evidence.py` validates a completed evidence record. It does not launch a browser, generate browser acceptance automatically, authorize credential processing, add the Argon2id artifacts to the production release, or authorize RC/Stable promotion.

## Evidence boundary

A passing CI run for this validator proves only that the evidence schema and fail-closed rules are internally enforced. It must never be treated as proof that a real browser was exercised.

The retained evidence must bind the run to:

- the full GoreeVault source revision;
- the SHA-256 identity of the validation-only browser candidate manifest;
- the exact generated JavaScript glue and WebAssembly SHA-256 identities;
- browser name, exact version, engine, operating system, and architecture;
- the HTTPS origin used for the browser run;
- the effective Content Security Policy and an empty CSP-violation list;
- real generated-binding loading and WebAssembly initialization;
- retained Bitwarden interoperability and GoreeVault authentication-material equivalence;
- explicit same-origin loading and explicit provider handoff;
- at least three timing samples with p50, p95, and maximum derivation time;
- a documented browser memory-observation method and before/after/peak values;
- an explicit `leakSuspected: false` result after review.

## Fail-closed approval state

Even a passing real-browser evidence record must retain:

- `credentialProcessingApproved: false`;
- `productionReleaseApproved: false`;
- `stablePromotionApproved: false`.

Real-browser validation is evidence for a later review. It is not itself authorization to process a master password, publish the generated browser bindings, deploy GoreeVault Web, create a release candidate, or declare Stable.

## Example shape

```json
{
  "schema": 1,
  "evidenceType": "goreevault-web-argon2id-real-browser",
  "sourceRevision": "<40-character-git-sha>",
  "candidateManifestSha256": "<sha256>",
  "browser": {
    "name": "Firefox",
    "version": "<exact-version>",
    "engine": "gecko",
    "os": "Linux",
    "architecture": "x86_64"
  },
  "servedOrigin": "https://<validation-origin>",
  "artifacts": {
    "javascriptPath": "goreevault_web_argon2id_core.js",
    "javascriptSha256": "<sha256>",
    "wasmPath": "goreevault_web_argon2id_core_bg.wasm",
    "wasmSha256": "<sha256>"
  },
  "execution": {
    "realBrowserExecuted": true,
    "generatedBindingsLoaded": true,
    "wasmInitialized": true,
    "bitwardenVectorPassed": true,
    "authenticationMaterialMatched": true,
    "sameOriginLoadObserved": true,
    "providerRegistrationWasExplicit": true
  },
  "csp": {
    "effectivePolicy": "<effective-policy>",
    "violations": []
  },
  "performance": {
    "samples": 5,
    "deriveMsP50": 0,
    "deriveMsP95": 0,
    "deriveMsMax": 0
  },
  "memory": {
    "method": "<browser-specific-observation-method>",
    "beforeBytes": 0,
    "afterBytes": 0,
    "peakBytes": 0,
    "leakSuspected": false
  },
  "approvals": {
    "credentialProcessingApproved": false,
    "productionReleaseApproved": false,
    "stablePromotionApproved": false
  },
  "accepted": true
}
```

The example contains placeholders and zero values and is therefore not itself valid acceptance evidence.

## Completion rule

This readiness slice is complete only when a real supported browser run produces evidence that passes the validator and is retained against the exact candidate artifacts. Until then, the real-browser performance, memory, CSP, and compatibility blocker remains open.
