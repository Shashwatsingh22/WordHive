"""
Environment loader for WordHive.

Loads the correct .env file based on ENV_FILE environment variable.

Usage:
    python bot.py                     → loads .env (default)
    ENV_FILE=.env.dev python bot.py   → loads .env.dev
    ENV_FILE=.env.prod python bot.py  → loads .env.prod
"""

import os
from dotenv import load_dotenv


def load_env():
    env_file = os.getenv("ENV_FILE", ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
    else:
        raise FileNotFoundError(f"Environment file not found: {env_file}")
