-- Start here: create the database and the users table.
CREATE DATABASE IF NOT EXISTS fitnut;
USE fitnut;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    status ENUM('active', 'suspended') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_online DATETIME
);

CREATE TABLE IF NOT EXISTS user_goals (
    user_id INT NOT NULL PRIMARY KEY,
    fitness_goal ENUM(
        'maintain',
        'lose_weight',
        'gain_muscle',
        'improve_fitness'
    ) NOT NULL,
    daily_calorie_target INT UNSIGNED NOT NULL,
    weekly_activity_minutes INT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_goals_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_daily_calorie_target
        CHECK (daily_calorie_target > 0),

    CONSTRAINT chk_weekly_activity_minutes
        CHECK (weekly_activity_minutes > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_reminders (
    reminder_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    reminder_type ENUM('meal', 'workout', 'water', 'weigh_in') NOT NULL,
    reminder_time TIME NOT NULL,
    frequency ENUM('daily', 'weekly') NOT NULL,
    weekday TINYINT UNSIGNED,
    notification_method ENUM('in_app', 'browser') NOT NULL DEFAULT 'in_app',
    motivation_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    utc_offset_minutes SMALLINT NOT NULL DEFAULT 0,
    last_due_date DATE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_reminders_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_reminder_weekday
        CHECK (weekday IS NULL OR weekday BETWEEN 0 AND 6),
    CONSTRAINT chk_reminder_offset
        CHECK (utc_offset_minutes BETWEEN -840 AND 840)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reminder_notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    reminder_id INT NOT NULL,
    user_id INT NOT NULL,
    message VARCHAR(300) NOT NULL,
    status ENUM('pending', 'snoozed', 'dismissed') NOT NULL DEFAULT 'pending',
    due_at DATETIME NOT NULL,
    snoozed_until DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notification_reminder
        FOREIGN KEY (reminder_id) REFERENCES user_reminders(reminder_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_notification_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    KEY idx_notifications_user_status (user_id, status)
) ENGINE=InnoDB;