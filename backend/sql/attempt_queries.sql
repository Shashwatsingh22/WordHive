-- Word attempt runtime queries

-- name: create_attempt
INSERT INTO app_word_attempts (id, session_id, word, user_spelling, is_correct, attempt_number, add_date)
VALUES (:id, :session_id, :word, :user_spelling, :is_correct, :attempt_number, :add_date);

-- name: get_attempts_by_session
SELECT id, session_id, word, user_spelling, is_correct, attempt_number, add_date
FROM app_word_attempts
WHERE session_id = :session_id
ORDER BY attempt_number ASC;
