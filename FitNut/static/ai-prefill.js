"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ai-form");

  if (!form) return;

  const params = new URLSearchParams(
    window.location.search
  );

  const allowed = {
    meal: [
      "diet",
      "calorie_target",
      "duration_days",
      "meals_per_day",
      "goal"
    ],
    workout: [
      "fitness_level",
      "days_per_week",
      "session_minutes",
      "equipment",
      "goal"
    ],
    nutrition: [
      "focus"
    ]
  };

  const feature = form.dataset.feature;

  for (const name of allowed[feature] || []) {
    if (!params.has(name)) continue;

    const field = form.elements.namedItem(name);

    if (!field || !("value" in field)) continue;

    const value = params.get(name);

    if (value === null || value.length > 300) {
      continue;
    }

    if (field.tagName === "SELECT") {
      const valid = Array.from(
        field.options
      ).some(option => option.value === value);

      if (!valid) continue;
    }

    if (field.type === "number") {
      const number = Number(value);

      if (!Number.isFinite(number)) continue;

      if (
        field.min &&
        number < Number(field.min)
      ) continue;

      if (
        field.max &&
        number > Number(field.max)
      ) continue;
    }

    field.value = value;
  }
});