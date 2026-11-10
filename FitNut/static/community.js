"use strict";

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-challenge-join]")
    .forEach(button => {
      button.addEventListener("click", async () => {
        button.disabled = true;

        try {
          const id = button.dataset.challengeJoin;

          await sendJSON(
            `/api/community/challenges/${id}/join`,
            "POST",
            {}
          );

          window.location.reload();
        } catch (error) {
          showNotice(error.message, true);
          button.disabled = false;
        }
      });
    });

  document.querySelectorAll("[data-challenge-progress]")
    .forEach(button => {
      button.addEventListener("click", async () => {
        try {
          const id = button.dataset.challengeProgress;

          const result = await sendJSON(
            `/api/community/challenges/${id}/progress`,
            "GET"
          );

          showNotice(
            `${result.minutes} of ` +
            `${result.target_minutes} minutes completed` +
            (result.completed ? " — Goal reached!" : "")
          );
        } catch (error) {
          showNotice(error.message, true);
        }
      });
    });

  document.querySelectorAll("[data-unblock]")
    .forEach(button => {
      button.addEventListener("click", async () => {
        button.disabled = true;

        try {
          await sendJSON(
            "/api/community/unblock",
            "POST",
            { user_id: button.dataset.unblock }
          );

          window.location.reload();
        } catch (error) {
          showNotice(error.message, true);
          button.disabled = false;
        }
      });
    });
});