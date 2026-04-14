"""
Database configuration for WordHive.

Handles:
    - SQLite connection via aiosqlite
    - Executing versioned .sql migration/seed files on startup
"""

from __future__ import annotations

import glob
import os

import aiosqlite
from loguru import logger

from config.constants import DEFAULT_DATABASE_PATH, ENV_DATABASE_PATH

DATABASE_PATH = os.getenv(ENV_DATABASE_PATH, DEFAULT_DATABASE_PATH)
MIGRATION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "migration_files")


def get_db_path() -> str:
    """Get absolute path to the SQLite database file."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", DATABASE_PATH
    )


async def get_connection() -> aiosqlite.Connection:
    """Get a new async database connection."""
    conn = await aiosqlite.connect(get_db_path())
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    return conn


async def run_sql_files():
    """
    Execute all versioned .sql files from the migration_files/ directory.

    Files follow Flyway naming: V1__description.sql, V2__description.sql
    Executed in sorted order to respect dependencies.
    """
    sql_files = sorted(glob.glob(os.path.join(MIGRATION_DIR, "V*.sql")))

    if not sql_files:
        logger.warning(f"No .sql files found in {MIGRATION_DIR}")
        return

    async with aiosqlite.connect(get_db_path()) as db:
        for sql_file in sql_files:
            filename = os.path.basename(sql_file)
            try:
                with open(sql_file, "r") as f:
                    sql = f.read()
                await db.executescript(sql)
                logger.info(f"Executed: {filename}")
            except Exception as e:
                logger.error(f"Failed to execute {filename}: {e}")
                raise

        await db.commit()

    logger.info("All SQL files executed successfully.")


async def init_db():
    """Initialize the database: run migration files to create tables and seed data."""
    await run_sql_files()
    logger.info("Database initialized.")


def load_query(filepath: str, query_name: str) -> str:
    """
    Load a named query from a .sql file.

    Queries are separated by '-- name: query_name' comments.
    """
    sql_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql")
    full_path = os.path.join(sql_dir, filepath)

    with open(full_path, "r") as f:
        content = f.read()

    queries = {}
    current_name = None
    current_lines = []

    for line in content.split("\n"):
        if line.strip().startswith("-- name:"):
            if current_name:
                queries[current_name] = "\n".join(current_lines).strip()
            current_name = line.strip().replace("-- name:", "").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_name:
        queries[current_name] = "\n".join(current_lines).strip()

    if query_name not in queries:
        raise ValueError(f"Query '{query_name}' not found in {filepath}")

    return queries[query_name]
