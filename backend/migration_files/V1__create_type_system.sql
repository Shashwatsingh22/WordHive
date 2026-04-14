-- Type system tables for WordHive
-- app_type_group: Groups of type values (e.g. session_status)
-- app_type: Individual type values belonging to a group
-- IDs are manually assigned by developers (no autoincrement)

CREATE TABLE IF NOT EXISTS app_type_group (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    add_date    DATETIME NOT NULL,
    update_date DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS app_type (
    id          INTEGER PRIMARY KEY,
    group_id    INTEGER NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    add_date    DATETIME NOT NULL,
    update_date DATETIME NOT NULL,

    FOREIGN KEY (group_id) REFERENCES app_type_group(id)
);
