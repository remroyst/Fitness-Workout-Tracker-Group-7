/* Batch 6 — UC12 Recipe Video Demonstrations */

const recipeForm = document.getElementById('recipe-form');
const recipeDataElement = document.getElementById('recipe-data');

const recipes = recipeDataElement
  ? JSON.parse(recipeDataElement.textContent)
  : [];

let editingRecipeId = null;

if (recipeForm) {
  recipeForm.addEventListener('submit', async event => {
    event.preventDefault();

    const message = recipeForm.querySelector('.form-message');
    const submit = document.getElementById('recipe-submit');

    message.hidden = true;
    submit.disabled = true;

    const values = Object.fromEntries(
      new FormData(recipeForm)
    );

    try {
      const result = await sendJSON(
        editingRecipeId
          ? `/recipes/${editingRecipeId}`
          : '/recipes',
        editingRecipeId ? 'PUT' : 'POST',
        values
      );

      sessionStorage.setItem('fitnut_notice', result.message);
      window.location.href = '/recipes';

    } catch (error) {
      message.textContent = error.message;
      message.hidden = false;
      submit.disabled = false;
    }
  });

  document.querySelectorAll('[data-recipe-edit]').forEach(button => {
    button.addEventListener('click', () => {
      const recipe = recipes.find(
        item => String(item.recipe_id) === button.dataset.recipeEdit
      );

      if (!recipe) return;

      editingRecipeId = recipe.recipe_id;

      const fields = [
        'title',
        'description',
        'ingredients',
        'instructions',
        'category',
        'preparation_minutes',
        'servings'
      ];

      for (const field of fields) {
        recipeForm.elements[field].value = recipe[field] ?? '';
      }

      recipeForm.elements.video_url.value =
        `https://www.youtube.com/watch?v=${recipe.youtube_video_id}`;

      document.getElementById('recipe-form-heading').textContent =
        'Edit Recipe';

      document.getElementById('recipe-submit').textContent =
        'Save Changes';

      document.getElementById('cancel-recipe-edit').hidden = false;

      recipeForm.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    });
  });

  document.getElementById('cancel-recipe-edit')
    .addEventListener('click', () => {
      editingRecipeId = null;
      recipeForm.reset();

      document.getElementById('recipe-form-heading').textContent =
        'Share a Recipe';

      document.getElementById('recipe-submit').textContent =
        'Add Recipe';

      document.getElementById('cancel-recipe-edit').hidden = true;
    });
}

document.querySelectorAll('[data-recipe-action]').forEach(button => {
  button.addEventListener('click', async () => {
    if (
      button.dataset.confirm &&
      !window.confirm(button.dataset.confirm)
    ) {
      return;
    }

    button.disabled = true;

    try {
      const result = await sendJSON(
        button.dataset.recipeAction,
        button.dataset.method || 'POST',
        button.dataset.method === 'DELETE' ? undefined : {}
      );

      sessionStorage.setItem('fitnut_notice', result.message);
      window.location.reload();

    } catch (error) {
      showNotice(error.message, true);
      button.disabled = false;
    }
  });
});