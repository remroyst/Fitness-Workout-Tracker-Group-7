"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("workout-details-form");
  const recordsContainer = document.getElementById("extended-records");

  const workouts = JSON.parse(
    document.getElementById("workout-data").textContent
  );

  function fillWorkout() {
    if (!form) return;

    const id = form.elements.activity_event_id.value;
    const workout = workouts.find(
      item => String(item.activity_event_id) === id
    );

    if (!workout) return;

    for (const key of [
      "distance_km",
      "sets_completed",
      "repetitions"
    ]) {
      form.elements[key].value = workout[key] ?? "";
    }

    form.elements.intensity.value =
      workout.intensity || "moderate";
  }

  form?.elements.activity_event_id.addEventListener(
    "change",
    fillWorkout
  );

  fillWorkout();

  form?.addEventListener("submit", async event => {
    event.preventDefault();

    const button = form.querySelector('button[type="submit"]');
    const message = form.querySelector(".form-message");

    button.disabled = true;
    message.hidden = true;

    try {
      const data = Object.fromEntries(new FormData(form));
      const id = data.activity_event_id;
      delete data.activity_event_id;

      await sendJSON(
        `/api/activity/${id}/details`,
        "POST",
        data
      );

      window.location.reload();
    } catch (error) {
      message.textContent = error.message;
      message.hidden = false;
      button.disabled = false;
    }
  });

  async function loadRecords() {
    try {
      const response = await sendJSON(
        "/api/records/extended",
        "GET"
      );

      recordsContainer.replaceChildren();

      const labels = {
        longest_distance: "Longest distance (km)",
        most_sets: "Most sets",
        most_repetitions: "Most repetitions"
      };

      for (const [key, label] of Object.entries(labels)) {
        const item = document.createElement("article");
        item.className = "community-message";

        const heading = document.createElement("h3");
        heading.textContent = label;
        item.append(heading);

        const detail = document.createElement("p");
        const record = response[key];

        detail.textContent = record
          ? `${record.value} — ${record.activity} ` +
            `(${new Date(record.date).toLocaleDateString()})`
          : "No record yet";

        item.append(detail);
        recordsContainer.append(item);
      }
    } catch (error) {
      recordsContainer.textContent = error.message;
    }
  }

  loadRecords();
});