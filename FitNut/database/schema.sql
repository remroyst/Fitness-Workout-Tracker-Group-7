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

-- Batch 4: UC09 Body Measurements
CREATE TABLE IF NOT EXISTS body_measurements (
    measurement_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    measured_on DATE NOT NULL,
    weight_kg DECIMAL(6,2) NULL,
    waist_cm DECIMAL(6,2) NULL,
    hips_cm DECIMAL(6,2) NULL,
    chest_cm DECIMAL(6,2) NULL,
    arm_cm DECIMAL(6,2) NULL,
    thigh_cm DECIMAL(6,2) NULL,
    body_fat_percent DECIMAL(5,2) NULL,
    notes VARCHAR(1000) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_body_measurements_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_body_fat
        CHECK (body_fat_percent IS NULL
               OR body_fat_percent BETWEEN 0 AND 100),
    INDEX idx_body_measurements_user_date (user_id, measured_on)
) ENGINE=InnoDB;

-- Batch 5: UC08 Social Networking

CREATE TABLE IF NOT EXISTS friendships (
    friendship_id INT AUTO_INCREMENT PRIMARY KEY,
    requester_id INT NOT NULL,
    addressee_id INT NOT NULL,
    status ENUM('pending', 'accepted') NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_friend_requester
        FOREIGN KEY (requester_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_friend_addressee
        FOREIGN KEY (addressee_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_different_friends
        CHECK (requester_id <> addressee_id),
    UNIQUE KEY uq_friend_pair (requester_id, addressee_id),
    INDEX idx_friend_addressee (addressee_id, status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS social_posts (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content VARCHAR(1000) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_social_post_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    INDEX idx_social_posts_user_date (user_id, created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS social_likes (
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES social_posts(post_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS social_comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    user_id INT NOT NULL,
    content VARCHAR(500) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES social_posts(post_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    INDEX idx_social_comments_post (post_id, created_at)
) ENGINE=InnoDB;

-- Batch 6: UC12 Recipe Video Demonstrations

CREATE TABLE IF NOT EXISTS video_recipes (
    recipe_id INT AUTO_INCREMENT PRIMARY KEY,
    created_by INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description VARCHAR(1000),
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL,
    youtube_video_id VARCHAR(11) NOT NULL,
    preparation_minutes INT UNSIGNED NOT NULL,
    servings INT UNSIGNED NOT NULL,
    category ENUM(
        'breakfast', 'lunch', 'dinner', 'snack'
    ) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_video_recipe_creator
        FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    INDEX idx_video_recipe_category (category)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS saved_video_recipes (
    user_id INT NOT NULL,
    recipe_id INT NOT NULL,
    saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, recipe_id),
    FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id)
        REFERENCES video_recipes(recipe_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Non-AI feature extensions.

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INT PRIMARY KEY,
    birth_date DATE NULL,
    height_cm DECIMAL(6,2) NULL,
    fitness_level ENUM('beginner','intermediate','advanced')
        NOT NULL DEFAULT 'beginner',
    dietary_preferences VARCHAR(500) NOT NULL DEFAULT '',
    allergies VARCHAR(500) NOT NULL DEFAULT '',
    intolerances VARCHAR(500) NOT NULL DEFAULT '',
    unit_system ENUM('metric','imperial')
        NOT NULL DEFAULT 'metric',
    profile_visibility ENUM('private','friends','public')
        NOT NULL DEFAULT 'friends',
    bio VARCHAR(500) NOT NULL DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS social_blocks (
    blocker_id INT NOT NULL,
    blocked_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (blocker_id, blocked_id),
    FOREIGN KEY (blocker_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (blocked_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CHECK (blocker_id <> blocked_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS social_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    content VARCHAR(2000) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME NULL,
    FOREIGN KEY (sender_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    INDEX idx_messages_recipient (recipient_id, created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS social_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id INT NOT NULL,
    reported_user_id INT NOT NULL,
    post_id INT NULL,
    reason VARCHAR(500) NOT NULL,
    status ENUM('pending','reviewed','resolved')
        NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (reported_user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES social_posts(post_id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fitness_challenges (
    challenge_id INT AUTO_INCREMENT PRIMARY KEY,
    creator_id INT NOT NULL,
    title VARCHAR(120) NOT NULL,
    description VARCHAR(500) NOT NULL DEFAULT '',
    target_minutes INT UNSIGNED NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    FOREIGN KEY (creator_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CHECK (target_minutes > 0),
    CHECK (end_date >= start_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS challenge_participants (
    challenge_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (challenge_id, user_id),
    FOREIGN KEY (challenge_id)
        REFERENCES fitness_challenges(challenge_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS activity_details (
    activity_event_id INT PRIMARY KEY,
    distance_km DECIMAL(10,3) NULL,
    sets_completed INT UNSIGNED NULL,
    repetitions INT UNSIGNED NULL,
    intensity ENUM('low','moderate','high')
        NOT NULL DEFAULT 'moderate',
    FOREIGN KEY (activity_event_id)
        REFERENCES activity_events(activity_event_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recipe_nutrition (
    recipe_id INT PRIMARY KEY,
    calories_per_serving DECIMAL(10,2) NULL,
    protein_g DECIMAL(10,2) NULL,
    carbs_g DECIMAL(10,2) NULL,
    fat_g DECIMAL(10,2) NULL,
    FOREIGN KEY (recipe_id)
        REFERENCES video_recipes(recipe_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;