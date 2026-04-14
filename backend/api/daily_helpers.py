"""
Daily REST API helpers.

Handles room creation and token generation via Daily's REST API.
"""

import os
import time

import aiohttp

from config.constants import (
    ENV_DAILY_API_KEY,
    ENV_DAILY_API_URL,
    DEFAULT_DAILY_API_URL,
    MAX_SESSION_TIME_SECS,
)

DAILY_API_KEY = os.getenv(ENV_DAILY_API_KEY, "")
DAILY_API_URL = os.getenv(ENV_DAILY_API_URL, DEFAULT_DAILY_API_URL)


async def create_daily_room() -> dict:
    headers = {
        "Authorization": f"Bearer {DAILY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {
            "exp": int(time.time()) + MAX_SESSION_TIME_SECS,
            "enable_chat": False,
            "start_video_off": True,
            "start_audio_off": False,
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{DAILY_API_URL}/rooms", headers=headers, json=payload
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to create Daily room: {text}")
            return await resp.json()


async def get_daily_token(room_name: str) -> str:
    headers = {
        "Authorization": f"Bearer {DAILY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {
            "room_name": room_name,
            "exp": int(time.time()) + MAX_SESSION_TIME_SECS,
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{DAILY_API_URL}/meeting-tokens", headers=headers, json=payload
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to get Daily token: {text}")
            data = await resp.json()
            return data["token"]
