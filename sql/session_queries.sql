-- Session runtime queries

-- name: create_session
INSERT INTO app_sessions (id, player_id, status_id, total_words, correct_count, incorrect_count, score, add_date, update_date)
VALUES (:id, :player_id, :status_id, 0, 0, 0, 0, :add_date, :update_date);

-- name: get_session_by_id
SELECT s.id, s.player_id, s.status_id, s.total_words, s.correct_count,
       s.incorrect_count, s.score, s.add_date, s.update_date, s.ended_at
FROM app_sessions s
WHERE s.id = :id;

-- name: update_session_score
UPDATE app_sessions
SET total_words = :total_words,
    correct_count = :correct_count,
    incorrect_count = :incorrect_count,
    score = :score,
    update_date = :update_date
WHERE id = :id;

-- name: end_session
UPDATE app_sessions
SET status_id = :status_id,
    ended_at = :ended_at,
    update_date = :update_date
WHERE id = :id;

-- name: get_leaderboard
SELECT s.score, s.correct_count, s.total_words, s.add_date, p.name AS player_name
FROM app_sessions s
JOIN app_players p ON s.player_id = p.id
WHERE s.status_id = :completed_status_id
ORDER BY s.score DESC
LIMIT 10;
