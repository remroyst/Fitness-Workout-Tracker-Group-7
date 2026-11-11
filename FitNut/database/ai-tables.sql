CREATE TABLE IF NOT EXISTS ai_generations (
    generation_id BIGINT UNSIGNED
        NOT NULL AUTO_INCREMENT,

    user_id INT NOT NULL,

    feature ENUM(
        'meal',
        'workout',
        'nutrition'
    ) NOT NULL,

    title VARCHAR(160) NOT NULL,

    status ENUM(
        'draft',
        'accepted'
    ) NOT NULL DEFAULT 'draft',

    content_json JSON NOT NULL,

    created_at TIMESTAMP
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP
        NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (generation_id),

    INDEX idx_ai_user_feature (
        user_id,
        feature,
        created_at
    )
);