import { buildApiUrl } from './runtime-config.js';
import { normalizeApiFailure } from './api-errors.js';

const DEFAULT_TIMEOUT_MS = 15000;
const ALLOWED_METHODS = new Set(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']);

function combineAbortSignals(externalSignal, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort('timeout'), timeoutMs);

  const abortFromExternal = () => controller.abort(externalSignal?.reason ?? 'cancelled');
  if (externalSignal) {
    if (externalSignal.aborted) abortFromExternal();
    else externalSignal.addEventListener('abort', abortFromExternal, { once: true });
  }

  return {
    signal: controller.signal,
    dispose() {
      clearTimeout(timeout);
      if (externalSignal) externalSignal.removeEventListener('abort', abortFromExternal);
    },
  };
}

async function parseResponseBody(response) {
  const contentType = response.headers.get('content-type') || '';
  if (response.status === 204) return null;
  if (contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch (_) {
      return null;
    }
  }
  return null;
}

export async function requestApi(path, {
  method = 'GET',
  body = undefined,
  headers = {},
  signal = undefined,
  timeoutMs = DEFAULT_TIMEOUT_MS,
  locationOrigin = globalThis.location?.origin,
  fetchImpl = globalThis.fetch,
} = {}) {
  const normalizedMethod = String(method).toUpperCase();
  if (!ALLOWED_METHODS.has(normalizedMethod)) throw new TypeError('Unsupported API method.');
  if (!Number.isFinite(timeoutMs) || timeoutMs < 1000 || timeoutMs > 60000) {
    throw new RangeError('API timeout must be between 1000 and 60000 milliseconds.');
  }
  if (typeof fetchImpl !== 'function') throw new TypeError('A fetch implementation is required.');

  const url = buildApiUrl(path, locationOrigin);
  const abort = combineAbortSignals(signal, timeoutMs);
  const requestHeaders = new Headers(headers);
  requestHeaders.set('Accept', 'application/json');

  let requestBody;
  if (body !== undefined) {
    requestHeaders.set('Content-Type', 'application/json');
    requestBody = JSON.stringify(body);
  }

  try {
    const response = await fetchImpl(url, {
      method: normalizedMethod,
      headers: requestHeaders,
      body: requestBody,
      signal: abort.signal,
      credentials: 'same-origin',
      cache: 'no-store',
      redirect: 'error',
      referrerPolicy: 'same-origin',
    });
    const payload = await parseResponseBody(response);
    if (!response.ok) throw normalizeApiFailure({ status: response.status, payload });
    return Object.freeze({ status: response.status, payload });
  } catch (error) {
    if (error?.name === 'GoreeVaultApiError') throw error;
    throw normalizeApiFailure({ aborted: abort.signal.aborted });
  } finally {
    abort.dispose();
  }
}
