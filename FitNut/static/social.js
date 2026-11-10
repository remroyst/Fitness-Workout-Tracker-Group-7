/* Batch 5 — UC08 Social Networking */

document.querySelectorAll('[data-social-action]').forEach(button => {
  button.addEventListener('click', async () => {
    const question = button.dataset.confirm;

    if (question && !window.confirm(question)) {
      return;
    }

    button.disabled = true;

    try {
      const result = await sendJSON(
        button.dataset.socialAction,
        button.dataset.method || 'POST',
        button.dataset.method === 'DELETE' ? undefined : {}
      );

      sessionStorage.setItem(
        'fitnut_notice',
        result.message
      );

      window.location.reload();

    } catch (error) {
      showNotice(error.message, true);
      button.disabled = false;
    }
  });
});