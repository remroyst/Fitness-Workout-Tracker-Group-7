"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("almond-form");

  if (!form) return;

  const questionInput = document.getElementById(
    "almond-question"
  );

  const submitButton = document.getElementById(
    "almond-submit"
  );

  const responseBox = document.getElementById(
    "almond-response"
  );

  const answerElement = document.getElementById(
    "almond-answer"
  );

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) return;

    const csrfToken = document.querySelector(
      'meta[name="csrf-token"]'
    )?.content;

    if (!csrfToken) {
      responseBox.hidden = false;
      answerElement.textContent =
        "Your session has expired. Refresh and log in again.";
      return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Almond is thinking...";

    responseBox.hidden = false;
    answerElement.textContent =
      "Generating your answer...";

    try {
      const response = await fetch(
        "/api/ai/almond/ask",
        {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-CSRF-Token": csrfToken
          },
          body: JSON.stringify({
            question: question
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
          "Almond couldn't answer right now."
        );
      }

      answerElement.textContent = data.answer;

    } catch (error) {
      answerElement.textContent =
        error.message ||
        "Something went wrong. Please try again.";

    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Ask Almond";
    }
  });
});