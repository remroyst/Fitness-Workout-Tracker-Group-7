"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ai-form");

  if (!form) return;

  const feature = form.dataset.feature;

  const resultPanel = document.getElementById(
    "ai-result-panel"
  );

  const resultContent = document.getElementById(
    "ai-result-content"
  );

  const resultTitle = document.getElementById(
    "ai-result-title"
  );

  const resultStatus = document.getElementById(
    "ai-result-status"
  );

  const resultMessage = document.getElementById(
    "ai-result-message"
  );

  const formMessage = document.getElementById(
    "ai-form-message"
  );

  const generateButton = document.getElementById(
    "ai-generate-button"
  );

  let currentId = null;
  let currentData = null;
  let currentStatus = "draft";

  function createElement(tag, text = "") {
    const element = document.createElement(tag);
    element.textContent = String(text);
    return element;
  }

  function makeButton(label, callback) {
    const button = createElement("button", label);
    button.type = "button";
    button.addEventListener("click", callback);
    return button;
  }

  async function apiRequest(url, method = "GET", data) {
  const csrfElement = document.querySelector(
    'meta[name="csrf-token"]'
  );

  const headers = {
    "Accept": "application/json"
  };

  if (method !== "GET") {
    if (!csrfElement || !csrfElement.content) {
      throw new Error(
        "CSRF token is missing. Refresh the page and log in again."
      );
    }

    headers["X-CSRF-Token"] = csrfElement.content;
  }

  const options = {
    method: method,
    credentials: "same-origin",
    headers: headers
  };

  if (data !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }

  const response = await fetch(url, options);

  const result = await response.json().catch(() => {
    throw new Error(
      "The server returned an unexpected response."
    );
  });

  if (!response.ok) {
    throw new Error(
      result.error ||
      `Request failed with HTTP ${response.status}`
    );
  }

  return result;
}

  function editableField(parent, object, field, label) {
    if (!(field in object)) return;

    const value = object[field];

    const display = Array.isArray(value)
      ? value.join(", ")
      : String(value ?? "");

    const row = createElement(
      "p",
      `${label}: ${display}`
    );

    row.append(
      " ",
      makeButton("Edit", () => {
        const updated = window.prompt(
          `Edit ${label}`,
          display
        );

        if (updated === null) return;

        if (Array.isArray(value)) {
          object[field] = updated
            .split(",")
            .map(item => item.trim())
            .filter(Boolean);
        } else if (typeof value === "number") {
          const number = Number(updated);

          if (!Number.isFinite(number) || number < 0) {
            resultMessage.textContent =
              "Please enter a valid number.";
            return;
          }

          object[field] = number;
        } else {
          object[field] = updated.trim();
        }

        currentStatus = "draft";
        renderResult();
      })
    );

    parent.append(row);
  }

  function renderFields(parent, object, fields) {
    for (const [field, label] of fields) {
      editableField(parent, object, field, label);
    }
  }

  function foodLogLink(food) {
    const params = new URLSearchParams({
      food_name: food.food_name || food.name || "",
      quantity: String(food.quantity || 1),
      calories: String(food.calories ?? ""),
      protein_g: String(food.protein_g ?? ""),
      carbs_g: String(food.carbs_g ?? ""),
      fat_g: String(food.fat_g ?? "")
    });

    window.location.href =
      `/food?${params.toString()}`;
  }

  function workoutLogLink(day, exercise) {
    const params = new URLSearchParams({
      activity_name: exercise.name || "",
      duration_minutes: String(
        day.duration_minutes || 45
      ),
      notes: [
        exercise.name,
        `${exercise.sets} sets`,
        `${exercise.reps} reps`,
        `${exercise.rest_seconds} seconds rest`
      ].join(", ")
    });

    window.location.href =
      `/activity?${params.toString()}`;
  }

  function renderMeals() {
    currentData.days.forEach((day, dayIndex) => {
      const section = document.createElement("section");
      section.className = "ai-day";

      section.append(
        createElement(
          "h3",
          `Day ${day.day || dayIndex + 1}`
        )
      );

      day.meals.forEach((meal, mealIndex) => {
        const card = document.createElement("article");
        card.className = "ai-item";

        card.append(
          createElement("h4", meal.name || "Meal")
        );

        renderFields(card, meal, [
          ["meal_type", "Meal type"],
          ["name", "Name"],
          ["ingredients", "Ingredients"],
          ["portion", "Portion"],
          ["calories", "Calories"],
          ["protein_g", "Protein (g)"],
          ["carbs_g", "Carbs (g)"],
          ["fat_g", "Fat (g)"],
          ["instructions", "Instructions"]
        ]);

        card.append(
          makeButton("Remove meal", () => {
            day.meals.splice(mealIndex, 1);
            currentStatus = "draft";
            renderResult();
          })
        );

        card.append(
          makeButton("Open food log", () => {
            foodLogLink(meal);
          })
        );

        section.append(card);
      });

      resultContent.append(section);
    });
  }

  function renderWorkouts() {
    currentData.days.forEach((day, dayIndex) => {
      const section = document.createElement("section");
      section.className = "ai-day";

      section.append(
        createElement(
          "h3",
          day.day || `Day ${dayIndex + 1}`
        )
      );

      section.append(
        createElement(
          "p",
          `Focus: ${day.focus || "General"}`
        )
      );

      section.append(
        createElement(
          "p",
          `Duration: ${day.duration_minutes} minutes`
        )
      );

      if (day.warmup) {
        section.append(
          createElement(
            "p",
            `Warmup: ${day.warmup}`
          )
        );
      }

      day.exercises.forEach(
        (exercise, exerciseIndex) => {
          const card = document.createElement("article");
          card.className = "ai-item";

          card.append(
            createElement(
              "h4",
              exercise.name || "Exercise"
            )
          );

          renderFields(card, exercise, [
            ["name", "Exercise"],
            ["sets", "Sets"],
            ["reps", "Reps"],
            ["rest_seconds", "Rest (seconds)"],
            ["equipment", "Equipment"],
            ["instructions", "Instructions"]
          ]);

          card.append(
            makeButton("Remove exercise", () => {
              day.exercises.splice(exerciseIndex, 1);
              currentStatus = "draft";
              renderResult();
            })
          );

          card.append(
            makeButton("Open activity log", () => {
              workoutLogLink(day, exercise);
            })
          );

          section.append(card);
        }
      );

      if (day.cooldown) {
        section.append(
          createElement(
            "p",
            `Cooldown: ${day.cooldown}`
          )
        );
      }

      resultContent.append(section);
    });
  }

  function renderNutrition() {
    if (currentData.summary) {
      resultContent.append(
        createElement("p", currentData.summary)
      );
    }

    currentData.suggestions.forEach(
      (suggestion, index) => {
        const card = document.createElement("article");
        card.className = "ai-item";

        card.append(
          createElement(
            "h4",
            suggestion.food_name || "Suggestion"
          )
        );

        renderFields(card, suggestion, [
          ["food_name", "Food"],
          ["portion", "Portion"],
          ["quantity", "Quantity"],
          ["unit", "Unit"],
          ["calories", "Calories"],
          ["protein_g", "Protein (g)"],
          ["carbs_g", "Carbs (g)"],
          ["fat_g", "Fat (g)"],
          ["meal_type", "Meal type"],
          ["reason", "Reason"]
        ]);

        card.append(
          makeButton("Remove suggestion", () => {
            currentData.suggestions.splice(index, 1);
            currentStatus = "draft";
            renderResult();
          })
        );

        card.append(
          makeButton("Open food log", () => {
            foodLogLink(suggestion);
          })
        );

        resultContent.append(card);
      }
    );
  }

  function renderResult() {
    if (!currentData) return;

    resultPanel.hidden = false;
    resultContent.replaceChildren();

    resultTitle.textContent =
      currentData.title || "AI Generated Result";

    resultStatus.textContent =
      currentStatus === "accepted"
        ? "Accepted"
        : "Draft";

    if (feature === "meal") {
      renderMeals();
    } else if (feature === "workout") {
      renderWorkouts();
    } else {
      renderNutrition();
    }
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();

    generateButton.disabled = true;
    generateButton.textContent = "Generating...";
    formMessage.textContent = "";

    try {
      const values = Object.fromEntries(
        new FormData(form).entries()
      );

      const result = await apiRequest(
        `/api/ai/${feature}/generate`,
        "POST",
        values
      );

      currentId = result.generation_id;
      currentData = result.content;
      currentStatus = "draft";

      renderResult();

      resultMessage.textContent =
        "Generated successfully. Review your result.";

    } catch (error) {
      formMessage.textContent = error.message;

    } finally {
      generateButton.disabled = false;
      generateButton.textContent =
        "Generate with Gemini";
    }
  });

  document.querySelectorAll(
    "[data-open-generation]"
  ).forEach(button => {
    button.addEventListener("click", async () => {
      try {
        const result = await apiRequest(
          `/api/ai/${button.dataset.openGeneration}`,
          "GET"
        );

        currentId = result.generation_id;
        currentData = result.content;
        currentStatus = result.status;

        renderResult();

      } catch (error) {
        formMessage.textContent = error.message;
      }
    });
  });

  async function savePlan(status) {
    if (!currentId || !currentData) return;

    try {
      await apiRequest(
        `/api/ai/${currentId}`,
        "PUT",
        {
          content: currentData,
          status
        }
      );

      currentStatus = status;
      renderResult();

      resultMessage.textContent =
        "Saved successfully.";

    } catch (error) {
      resultMessage.textContent = error.message;
    }
  }

  document.getElementById("ai-save")
    .addEventListener("click", () => {
      savePlan("draft");
    });

  document.getElementById("ai-accept")
    .addEventListener("click", () => {
      savePlan("accepted");
    });

  document.getElementById("ai-delete")
    .addEventListener("click", async () => {
      if (!currentId) return;

      if (!window.confirm("Delete this plan?")) {
        return;
      }

      try {
        await apiRequest(
          `/api/ai/${currentId}`,
          "DELETE"
        );

        window.location.reload();

      } catch (error) {
        resultMessage.textContent = error.message;
      }
    });
});