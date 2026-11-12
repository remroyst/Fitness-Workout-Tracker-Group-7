"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const launcher = document.getElementById(
    "almond-launcher"
  );

  const panel = document.getElementById(
    "almond-floating-panel"
  );

  const close = document.getElementById(
    "almond-close"
  );

  if (!launcher || !panel || !close) return;

  function setOpen(open) {
    panel.hidden = !open;

    launcher.setAttribute(
      "aria-expanded",
      String(open)
    );

    if (open) {
      document.getElementById(
        "almond-question"
      )?.focus();
    } else {
      launcher.focus();
    }
  }

  launcher.addEventListener("click", () => {
    setOpen(panel.hidden);
  });

  close.addEventListener("click", () => {
    setOpen(false);
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !panel.hidden) {
      setOpen(false);
    }
  });

  const form = document.getElementById(
    "almond-form"
  );

  form?.addEventListener("submit", () => {
    launcher.classList.add("is-loading");
  });

  const answer = document.getElementById(
    "almond-answer"
  );

  if (answer) {
    const observer = new MutationObserver(() => {
      launcher.classList.remove("is-loading");
    });

    observer.observe(answer, {
      childList: true,
      characterData: true,
      subtree: true
    });
  }
});