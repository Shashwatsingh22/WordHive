-- Player runtime queries

-- name: create_player
INSERT INTO app_players (id, name, add_date, update_date)
VALUES (:id, :name, :add_date, :update_date);

-- name: get_player_by_id
SELECT id, name, add_date, update_date
FROM app_players
WHERE id = :id;
