"use strict";

(() => {
  const storageKey = "fitnut_theme";

  function getTheme() {
    try {
      return localStorage.getItem(storageKey) || "dark";
    } catch {
      return "dark";
    }
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem(storageKey, theme);
    } catch {
      // Theme still works during this session.
    }
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;

    const button = document.querySelector("[data-theme-toggle]");

    if (button) {
      button.textContent =
        theme === "dark" ? "☀ Light mode" : "☾ Dark mode";

      button.setAttribute(
        "aria-label",
        theme === "dark"
          ? "Switch to light mode"
          : "Switch to dark mode"
      );
    }
  }

  applyTheme(getTheme());

  document.addEventListener("DOMContentLoaded", () => {
    applyTheme(getTheme());

    document.querySelector("[data-theme-toggle]")
      ?.addEventListener("click", () => {
        const next =
          document.documentElement.dataset.theme === "dark"
            ? "light"
            : "dark";

        saveTheme(next);
        applyTheme(next);
      });
  });
})();