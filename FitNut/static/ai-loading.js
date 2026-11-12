"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ai-form");
  const button = document.getElementById(
    "ai-generate-button"
  );

  if (!form || !button) return;

  const messages = {
    meal: [
      "Reviewing your nutrition goals...",
      "Building your meal plan...",
      "Estimating calories and macros..."
    ],
    workout: [
      "Reviewing your fitness goals...",
      "Building your workout plan...",
      "Organizing your training sessions..."
    ],
    nutrition: [
      "Reviewing your food logs...",
      "Checking your nutrition goals...",
      "Preparing recommendations..."
    ]
  };

  const feature = form.dataset.feature;
  const sequence = messages[feature] || messages.meal;

  const loading = document.createElement("div");
  loading.className = "fitnut-ai-loading";
  loading.hidden = true;
  loading.setAttribute("role", "status");

  const almond = document.createElement("span");
  almond.className = "fitnut-loading-almond";
  almond.setAttribute("aria-hidden", "true");

  const text = document.createElement("span");

  loading.append(almond, text);
  form.append(loading);

  let interval = null;
  let index = 0;

  function stopLoading() {
    loading.hidden = true;
    clearInterval(interval);
    interval = null;
  }

  form.addEventListener("submit", () => {
    stopLoading();

    index = 0;
    text.textContent = sequence[index];
    loading.hidden = false;

    interval = setInterval(() => {
      index = (index + 1) % sequence.length;
      text.textContent = sequence[index];
    }, 2400);
  });

  const resultPanel = document.getElementById(
    "ai-result-panel"
  );

  const formMessage = document.getElementById(
    "ai-form-message"
  );

  const observer = new MutationObserver(() => {
    if (
      !button.disabled ||
      (resultPanel && !resultPanel.hidden) ||
      (formMessage && formMessage.textContent.trim())
    ) {
      stopLoading();
    }
  });

  observer.observe(button, {
    attributes: true,
    attributeFilter: ["disabled"]
  });

  if (resultPanel) {
    observer.observe(resultPanel, {
      attributes: true,
      attributeFilter: ["hidden"]
    });
  }

  if (formMessage) {
    observer.observe(formMessage, {
      childList: true,
      characterData: true,
      subtree: true
    });
  }
});