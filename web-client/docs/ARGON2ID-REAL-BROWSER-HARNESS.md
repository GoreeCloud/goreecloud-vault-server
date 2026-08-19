# GoreeVault Web Argon2id Real-Browser Harness

## Purpose

This validation-only harness closes the collection gap between generated browser candidate artifacts and the retained evidence validator. It exercises the reviewed synthetic Bitwarden interoperability vector in an actual browser, measures derivation timing, records available browser memory observations, captures CSP violations, and hashes the exact JavaScript and WebAssembly artifacts loaded by the page.

It is not a production GoreeVault Web screen and it is not an authorization path.

## Safety boundary

The harness intentionally:

- requires HTTPS;
- refuses cross-origin generated bindings;
- omits credentials from candidate-artifact fetches;
- uses only the reviewed synthetic interoperability secret and salt;
- records CSP violations rather than suppressing them;
- leaves `providerRegistrationWasExplicit` false;
- leaves credential-processing, production-release, and Stable approvals false;
- leaves `accepted` false.

Those false values are deliberate. The browser can collect observations, but it cannot self-approve architectural provider handoff, memory review, release status, or Stable promotion.

## Controlled use

1. Build the exact validation-only browser candidate artifacts through the existing candidate-evidence process.
2. Place the generated JavaScript and WebAssembly files beside the harness or at another same-origin HTTPS path.
3. Serve `web-client/validation/argon2id-real-browser/` from the controlled validation origin over HTTPS.
4. Enter the exact 40-character source revision and candidate-manifest SHA-256.
5. Run the synthetic browser acceptance operation.
6. Review browser name/version/engine, OS/architecture, CSP results, timing samples, and memory observations.
7. Independently verify the explicit GoreeVault provider-registration/handoff boundary.
8. Only after those reviews, prepare a retained evidence record for `validate_browser_argon2id_evidence.py`.

The downloaded JSON is therefore a collection record, not automatically valid final evidence. It must not be edited to claim observations or approvals that did not occur.

## Completion boundary

A successful CI run validates only the harness safety contract and evidence validator. Actual real-browser acceptance still requires an operator-run supported browser against exact generated artifacts and subsequent review. Production credential processing, release publication, RC promotion, and Stable promotion remain separate decisions.
