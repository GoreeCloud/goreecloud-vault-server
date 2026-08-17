export class GoreeVaultApiError extends Error {
  constructor(message, { status = 0, code = 'request_failed', retryable = false } = {}) {
    super(message);
    this.name = 'GoreeVaultApiError';
    this.status = Number.isInteger(status) ? status : 0;
    this.code = typeof code === 'string' && code ? code : 'request_failed';
    this.retryable = Boolean(retryable);
  }
}

function safeMessage(payload, fallback) {
  if (!payload || typeof payload !== 'object') return fallback;
  for (const key of ['message', 'Message', 'error_description', 'error']) {
    const value = payload[key];
    if (typeof value === 'string' && value.trim()) return value.trim().slice(0, 240);
  }
  return fallback;
}

export function normalizeApiFailure({ status = 0, payload = null, aborted = false } = {}) {
  if (aborted) {
    return new GoreeVaultApiError('The request was cancelled.', {
      status: 0,
      code: 'request_cancelled',
      retryable: false,
    });
  }

  if (!status) {
    return new GoreeVaultApiError('GoreeVault Server could not be reached.', {
      status: 0,
      code: 'network_unavailable',
      retryable: true,
    });
  }

  const retryable = status === 408 || status === 425 || status === 429 || status >= 500;
  const fallback = status === 401 || status === 403
    ? 'The server rejected this authentication state.'
    : `GoreeVault Server returned HTTP ${status}.`;

  return new GoreeVaultApiError(safeMessage(payload, fallback), {
    status,
    code: status === 401 ? 'authentication_required' : `http_${status}`,
    retryable,
  });
}
