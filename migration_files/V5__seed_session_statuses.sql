-- Seed data: session status type group and types
-- IDs are manually assigned to match Python enums

INSERT OR IGNORE INTO app_type_group (id, name, description, add_date, update_date)
VALUES (1, 'session_status', 'Status values for game sessions', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT OR IGNORE INTO app_type (id, group_id, name, description, add_date, update_date)
VALUES (1, 1, 'in_progress', 'Game is currently being played', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT OR IGNORE INTO app_type (id, group_id, name, description, add_date, update_date)
VALUES (2, 1, 'completed', 'Game finished normally', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT OR IGNORE INTO app_type (id, group_id, name, description, add_date, update_date)
VALUES (3, 1, 'abandoned', 'Game was abandoned or disconnected', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
