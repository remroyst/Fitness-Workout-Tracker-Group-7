/* Batch 4 — UC09 Body Measurements */

const measurementForm =
  document.getElementById('measurement-form');

const measurementRecords = JSON.parse(
  document.getElementById('measurement-data').textContent
);

const measurementFields = [
  'measured_on',
  'weight_kg',
  'waist_cm',
  'hips_cm',
  'chest_cm',
  'arm_cm',
  'thigh_cm',
  'body_fat_percent',
  'notes'
];

let editingMeasurementId = null;

measurementForm.addEventListener('submit', async event => {
  event.preventDefault();

  const message =
    measurementForm.querySelector('.form-message');

  const saveButton =
    measurementForm.querySelector('[type="submit"]');

  message.hidden = true;
  saveButton.disabled = true;

  const data = Object.fromEntries(
    new FormData(measurementForm)
  );

  try {
    const url = editingMeasurementId
      ? `/measurements/${editingMeasurementId}`
      : '/measurements';

    const method = editingMeasurementId
      ? 'PUT'
      : 'POST';

    const result = await sendJSON(url, method, data);

    sessionStorage.setItem(
      'fitnut_notice',
      result.message
    );

    window.location.reload();

  } catch (error) {
    message.textContent = error.message;
    message.hidden = false;
    saveButton.disabled = false;
  }
});


document
  .querySelectorAll('[data-measurement-edit]')
  .forEach(button => {
    button.addEventListener('click', () => {

      const record = measurementRecords.find(
        item => String(item.measurement_id)
          === button.dataset.measurementEdit
      );

      if (!record) return;

      editingMeasurementId = record.measurement_id;

      for (const field of measurementFields) {
        const input = measurementForm.elements.namedItem(field);

        if (input) {
          input.value = record[field] ?? '';
        }
      }

      document.getElementById(
        'measurement-form-title'
      ).textContent = 'Edit Body Measurements';

      measurementForm.querySelector(
        '[type="submit"]'
      ).textContent = 'Save Changes';

      document.getElementById(
        'cancel-measurement-edit'
      ).hidden = false;

      measurementForm.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    });
  });


document.getElementById(
  'cancel-measurement-edit'
).addEventListener('click', () => {

  editingMeasurementId = null;
  measurementForm.reset();

  document.getElementById(
    'measurement-form-title'
  ).textContent = 'Add Body Measurements';

  measurementForm.querySelector(
    '[type="submit"]'
  ).textContent = 'Save Measurements';

  document.getElementById(
    'cancel-measurement-edit'
  ).hidden = true;

  measurementForm.querySelector(
    '.form-message'
  ).hidden = true;
});


document
  .querySelectorAll('[data-measurement-delete]')
  .forEach(button => {
    button.addEventListener('click', async () => {

      if (!window.confirm(
        'Delete this body measurement entry?'
      )) {
        return;
      }

      button.disabled = true;

      try {
        const result = await sendJSON(
          `/measurements/${button.dataset.measurementDelete}`,
          'DELETE'
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