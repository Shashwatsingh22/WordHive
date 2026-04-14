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

DATABASE_PATH = os.getenv("DATABASE_PATH", "spellbee.db")
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
