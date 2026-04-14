-- Word attempts table for WordHive

CREATE TABLE IF NOT EXISTS app_word_attempts (
    id              VARCHAR(36) PRIMARY KEY,
    session_id      VARCHAR(36) NOT NULL,
    word            VARCHAR(100) NOT NULL,
    user_spelling   TEXT,
    is_correct      BOOLEAN,
    attempt_number  INTEGER NOT NULL,
    add_date        DATETIME,

    FOREIGN KEY (session_id) REFERENCES app_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_word_attempts_session_id ON app_word_attempts(session_id);
