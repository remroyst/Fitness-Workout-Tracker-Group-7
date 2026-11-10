const reminderForm = document.getElementById('reminder-form');
const frequencyInput = document.getElementById('reminder-frequency');
const weekdayField = document.getElementById('weekday-field');
const reminderOutput = document.getElementById('reminder-notifications');
const seenNotifications = new Set();

let editingReminderId = null;

function updateWeekday() {
  weekdayField.hidden = frequencyInput.value !== 'weekly';
}

frequencyInput.addEventListener('change', updateWeekday);
updateWeekday();

function reminderBody() {
  const values = Object.fromEntries(new FormData(reminderForm));

  return {
    reminder_type: values.reminder_type,
    reminder_time: values.reminder_time,
    frequency: values.frequency,
    weekday: values.weekday || null,
    notification_method: values.notification_method,
    motivation_enabled:
      reminderForm.elements.motivation_enabled.checked,
    enabled: reminderForm.elements.enabled.checked,
    utc_offset_minutes: -new Date().getTimezoneOffset()
  };
}

reminderForm.addEventListener('submit', async event => {
  event.preventDefault();

  const message = reminderForm.querySelector('.form-message');
  const button = reminderForm.querySelector('[type="submit"]');

  message.hidden = true;
  button.disabled = true;

  try {
    const method = editingReminderId ? 'PUT' : 'POST';
    const url = editingReminderId
      ? `/reminders/${editingReminderId}`
      : '/reminders';

    const body = reminderBody();

    if (
      body.notification_method === 'browser'
      && 'Notification' in window
      && Notification.permission === 'default'
    ) {
      await Notification.requestPermission();
    }

    const result = await sendJSON(url, method, body);

    sessionStorage.setItem('fitnut_notice', result.message);
    window.location.reload();
  } catch (error) {
    message.textContent = error.message;
    message.hidden = false;
    button.disabled = false;
  }
});

document.querySelectorAll('.reminder-edit').forEach(button => {
  button.addEventListener('click', () => {
    editingReminderId = button.dataset.id;

    reminderForm.elements.reminder_type.value = button.dataset.type;
    reminderForm.elements.reminder_time.value = button.dataset.time;
    reminderForm.elements.frequency.value = button.dataset.frequency;
    reminderForm.elements.weekday.value = button.dataset.weekday;
    reminderForm.elements.notification_method.value =
      button.dataset.method;
    reminderForm.elements.motivation_enabled.checked =
      button.dataset.motivation === '1';
    reminderForm.elements.enabled.checked =
      button.dataset.enabled === '1';

    updateWeekday();

    document.getElementById('reminder-form-title').textContent =
      'Edit reminder';
    document.getElementById('cancel-reminder-edit').hidden = false;

    reminderForm.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  });
});

document.getElementById('cancel-reminder-edit')
  .addEventListener('click', () => {
    editingReminderId = null;
    reminderForm.reset();
    updateWeekday();
    document.getElementById('reminder-form-title').textContent =
      'Add reminder';
    document.getElementById('cancel-reminder-edit').hidden = true;
  });

document.querySelectorAll('.reminder-delete').forEach(button => {
  button.addEventListener('click', async () => {
    if (!confirm('Delete this reminder?')) return;

    button.disabled = true;

    try {
      const result = await sendJSON(
        `/reminders/${button.dataset.id}`,
        'DELETE'
      );

      sessionStorage.setItem('fitnut_notice', result.message);
      window.location.reload();
    } catch (error) {
      showNotice(error.message, true);
      button.disabled = false;
    }
  });
});

document.getElementById('disable-all-reminders')
  ?.addEventListener('click', async () => {
    if (!confirm('Turn off all reminders and messages?')) return;

    try {
      const result = await sendJSON(
        '/reminders/disable-all',
        'POST',
        {}
      );

      sessionStorage.setItem('fitnut_notice', result.message);
      window.location.reload();
    } catch (error) {
      showNotice(error.message, true);
    }
  });

async function reminderAction(notificationId, action) {
  try {
    const result = await sendJSON(
      `/reminders/notifications/${notificationId}/${action}`,
      'POST',
      {}
    );

    showNotice(result.message);
    await pollReminders();
  } catch (error) {
    showNotice(error.message, true);
  }
}

async function pollReminders() {
  try {
    const result = await sendJSON('/reminders/check', 'POST', {});
    reminderOutput.replaceChildren();

    if (!result.notifications.length) {
      const empty = document.createElement('p');
      empty.className = 'muted';
      empty.textContent = 'No reminders due right now.';
      reminderOutput.appendChild(empty);
      return;
    }

    for (const item of result.notifications) {
      const container = document.createElement('div');
      container.className = 'reminder-item';

      const message = document.createElement('p');
      message.textContent = item.message;
      container.appendChild(message);

      const snooze = document.createElement('button');
      snooze.type = 'button';
      snooze.textContent = 'Snooze 10 minutes';
      snooze.addEventListener('click', () =>
        reminderAction(item.notification_id, 'snooze')
      );

      const dismiss = document.createElement('button');
      dismiss.type = 'button';
      dismiss.textContent = 'Dismiss';
      dismiss.addEventListener('click', () =>
        reminderAction(item.notification_id, 'dismiss')
      );

      container.append(snooze, dismiss);

      if (item.reminder_type === 'meal') {
        const link = document.createElement('a');
        link.href = '/food';
        link.textContent = 'Open Food Log';
        container.appendChild(link);
      }

      if (item.reminder_type === 'workout') {
        const link = document.createElement('a');
        link.href = '/activity';
        link.textContent = 'Open Activity Log';
        container.appendChild(link);
      }

      reminderOutput.appendChild(container);

      if (!seenNotifications.has(item.notification_id)) {
        seenNotifications.add(item.notification_id);

        if (
          item.notification_method === 'browser'
          && 'Notification' in window
          && Notification.permission === 'granted'
        ) {
          new Notification('FitNut Reminder', {
            body: item.message
          });
        }
      }
    }
  } catch (error) {
    console.error('Reminder check failed:', error);
  }
}

pollReminders();
setInterval(pollReminders, 60000);