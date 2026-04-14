-- Game sessions table for WordHive

CREATE TABLE IF NOT EXISTS app_sessions (
    id              VARCHAR(36) PRIMARY KEY,
    player_id       VARCHAR(36) NOT NULL,
    status_id       INTEGER NOT NULL,
    total_words     INTEGER DEFAULT 0,
    correct_count   INTEGER DEFAULT 0,
    incorrect_count INTEGER DEFAULT 0,
    score           INTEGER DEFAULT 0,
    add_date        DATETIME,
    update_date     DATETIME,
    ended_at        DATETIME,

    FOREIGN KEY (player_id) REFERENCES app_players(id),
    FOREIGN KEY (status_id) REFERENCES app_type(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_player_id ON app_sessions(player_id);
