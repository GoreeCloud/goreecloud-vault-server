(() => {
  const key = 'goreevault-web-appearance';
  let value = 'system';
  try {
    const stored = localStorage.getItem(key);
    if (stored === 'light' || stored === 'dark') value = stored;
    else if (stored !== null) localStorage.removeItem(key);
  } catch (_) {
    // Browser storage is optional for appearance preference.
  }
  document.documentElement.dataset.appearance = value;
})();
