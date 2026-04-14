-- Players table for WordHive

CREATE TABLE IF NOT EXISTS app_players (
    id          VARCHAR(36) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    add_date    DATETIME,
    update_date DATETIME
);
