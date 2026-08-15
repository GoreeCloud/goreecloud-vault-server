"use strict";
/* exported BASE_URL, _post, _delete */

function getBaseUrl() {
    const pathname = window.location.pathname;
    const adminPos = pathname.indexOf("/admin");
    const newPathname = pathname.substring(0, adminPos !== -1 ? adminPos : pathname.length);
    return `${window.location.origin}${newPathname}`;
}
const BASE_URL = getBaseUrl();

function reload() {
    // Setting the same href avoids a browser repost prompt that reload() can trigger.
    window.location = window.location.href;
}

function msg(text, reload_page = true) {
    text && alert(text);
    reload_page && reload();
}

function _fetch(method, url, successMsg, errMsg, body, reload_page = true) {
    let respStatus;
    let respStatusText;
    fetch(url, {
        method: method,
        body: body,
        mode: "same-origin",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" }
    }).then(resp => {
        if (resp.ok) {
            msg(successMsg, reload_page);
            return Promise.reject({ error: false });
        }
        respStatus = resp.status;
        respStatusText = resp.statusText;
        return resp.text();
    }).then(respText => {
        try {
            const respJson = JSON.parse(respText);
            if (respJson.errorModel && respJson.errorModel.message) {
                return respJson.errorModel.message;
            }
            return Promise.reject({ body: `${respStatus} - ${respStatusText}\n\nUnknown error`, error: true });
        } catch (e) {
            return Promise.reject({ body: `${respStatus} - ${respStatusText}\n\n[Catch] ${e}`, error: true });
        }
    }).then(apiMsg => {
        msg(`${errMsg}\n${apiMsg}`, reload_page);
    }).catch(e => {
        if (e.error === false) return true;
        msg(`${errMsg}\n${e.body}`, reload_page);
    });
}

function _post(url, successMsg, errMsg, body, reload_page = true) {
    return _fetch("POST", url, successMsg, errMsg, body, reload_page);
}

function _delete(url, successMsg, errMsg, body, reload_page = true) {
    return _fetch("DELETE", url, successMsg, errMsg, body, reload_page);
}

// GoreeCloud Glaze appearance preference. Only explicit Light/Dark overrides
// persist; System removes the override. This state never leaves the browser.
const THEME_STORAGE_KEY = "goreecloud-goreevault-theme";
const VALID_THEMES = new Set(["system", "light", "dark"]);

function getStoredTheme() {
    try {
        const value = window.localStorage.getItem(THEME_STORAGE_KEY);
        return value === "light" || value === "dark" ? value : null;
    } catch (_error) {
        return null;
    }
}

function setStoredTheme(theme) {
    try {
        if (theme === "system") {
            window.localStorage.removeItem(THEME_STORAGE_KEY);
        } else {
            window.localStorage.setItem(THEME_STORAGE_KEY, theme);
        }
    } catch (_error) {
        // Browser-local storage is optional. System/in-memory behavior remains usable.
    }
}

function getPreferredTheme() {
    return getStoredTheme() || "system";
}

function resolvedTheme(theme) {
    if (theme === "system") {
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return theme;
}

function setTheme(theme) {
    const safeTheme = VALID_THEMES.has(theme) ? theme : "system";
    document.documentElement.setAttribute("data-theme", safeTheme);
    document.documentElement.setAttribute("data-bs-theme", resolvedTheme(safeTheme));
}

// Runs in <head> before the stylesheets so explicit appearance is applied to first paint.
setTheme(getPreferredTheme());

function showActiveTheme(theme, focus = false) {
    const safeTheme = VALID_THEMES.has(theme) ? theme : "system";
    const themeSwitcher = document.querySelector("#bd-theme");
    if (!themeSwitcher) return;

    const themeSwitcherText = document.querySelector("#bd-theme-text");
    const activeThemeIcon = document.querySelector(".theme-icon-active use");
    const btnToActive = document.querySelector(`[data-bs-theme-value="${safeTheme}"]`);
    if (!btnToActive) return;

    const btnIconUse = btnToActive.querySelector("[data-theme-icon-use]");
    const iconHref = btnIconUse ? btnIconUse.getAttribute("href") || btnIconUse.getAttribute("xlink:href") : null;

    document.querySelectorAll("[data-bs-theme-value]").forEach(element => {
        element.classList.remove("active");
        element.setAttribute("aria-pressed", "false");
    });

    btnToActive.classList.add("active");
    btnToActive.setAttribute("aria-pressed", "true");

    if (iconHref && activeThemeIcon) {
        activeThemeIcon.setAttribute("href", iconHref);
        activeThemeIcon.setAttribute("xlink:href", iconHref);
    }

    const labelText = themeSwitcherText ? themeSwitcherText.textContent : "Appearance";
    themeSwitcher.setAttribute("aria-label", `${labelText} (${btnToActive.textContent.trim()})`);

    if (focus) themeSwitcher.focus();
}

const colorScheme = window.matchMedia("(prefers-color-scheme: dark)");
colorScheme.addEventListener("change", () => {
    if (!getStoredTheme()) setTheme("system");
});

document.addEventListener("DOMContentLoaded", () => {
    // Upstream admin partials already own the semantic <main> landmark. Give the
    // first one a stable Glaze skip target without rewriting every upstream partial.
    const main = document.querySelector("main");
    if (main && !document.getElementById("gv-main")) {
        main.id = "gv-main";
        main.setAttribute("tabindex", "-1");
    }

    showActiveTheme(getPreferredTheme());

    document.querySelectorAll("[data-bs-theme-value]").forEach(toggle => {
        toggle.addEventListener("click", () => {
            const theme = toggle.getAttribute("data-bs-theme-value") || "system";
            if (!VALID_THEMES.has(theme)) return;
            setStoredTheme(theme);
            setTheme(theme);
            showActiveTheme(theme, true);
        });
    });

    const pathname = window.location.pathname;
    if (!pathname) return;
    const navItems = document.querySelectorAll(`.navbar-nav .nav-item a[href="${pathname}"]`);
    if (navItems.length === 1) {
        navItems[0].classList.add("active");
        navItems[0].setAttribute("aria-current", "page");
    }
});
