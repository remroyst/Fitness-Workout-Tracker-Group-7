"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById(
    "almond-form"
  );

  const question = document.getElementById(
    "almond-question"
  );

  const response = document.getElementById(
    "almond-response"
  );

  if (!form || !question || !response) return;

  const links = document.createElement("div");
  links.id = "almond-planner-links";

  response.append(links);

  function plannerSuggestion(text) {
    const input = text.toLowerCase();
    const params = new URLSearchParams();

    let path = null;
    let label = null;

    if (
      /\b(workout|exercise|training)\b/.test(input)
    ) {
      path = "/ai/workout";
      label = "Open Workout Planner";

      const level = input.match(
        /\b(beginner|intermediate|advanced)\b/
      );

      if (level) {
        params.set("fitness_level", level[1]);
      }

      const days = input.match(
        /\b([1-7])\s*days?\b/
      );

      if (days) {
        params.set("days_per_week", days[1]);
      }

      const minutes = input.match(
        /\b(\d{2,3})\s*(minutes?|mins?)\b/
      );

      if (minutes) {
        const value = Number(minutes[1]);

        if (value >= 10 && value <= 180) {
          params.set("session_minutes", String(value));
        }
      }

      if (/\b(bodyweight|no equipment)\b/.test(input)) {
        params.set("equipment", "Bodyweight");
      }
    } else if (
      /\b(meal plan|meal planning|meal planner)\b/.test(input)
    ) {
      path = "/ai/meal";
      label = "Open Meal Planner";

      const days = input.match(
        /\b(1|7)\s*days?\b/
      );

      if (days) {
        params.set("duration_days", days[1]);
      }

      const calories = input.match(
        /\b(\d{3,4})\s*(calories|kcal)\b/
      );

      if (calories) {
        const value = Number(calories[1]);

        if (value >= 800 && value <= 6000) {
          params.set("calorie_target", String(value));
        }
      }

      const diets = [
        "vegetarian",
        "vegan",
        "high protein",
        "gluten free",
        "low carb"
      ];

      const diet = diets.find(item =>
        input.includes(item)
      );

      if (diet) {
        params.set("diet", diet);
      }
    } else if (
      /\b(nutrition|healthy snacks|food suggestions)\b/.test(input)
    ) {
      path = "/ai/nutrition";
      label = "Open Nutrition Recommendations";

      params.set("focus", text.slice(0, 300));
    }

    if (!path) return null;

    return {
      label,
      url: `${path}?${params.toString()}`
    };
  }

  form.addEventListener("submit", () => {
    links.replaceChildren();

    const suggestion = plannerSuggestion(
      question.value.trim()
    );

    if (!suggestion) return;

    const link = document.createElement("a");

    link.className = "almond-prefill-link";
    link.href = suggestion.url;
    link.textContent = suggestion.label;

    links.append(link);
  });
});