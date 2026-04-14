"""
Bot Runner — Optional standalone FastAPI server for API endpoints.

The main entry point is bot.py which uses Pipecat's built-in runner.
This file provides additional REST endpoints (leaderboard, game state)
that can be run alongside the bot if needed.
"""

import os

from config.env import load_env
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config.constants import REQUIRED_ENV_VARS, SERVER_HOST, SERVER_PORT
from config.database import init_db
from api.game_routes import router as game_router

load_env()

app = FastAPI(title="WordHive — Spell Bee Voice Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)

frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.on_event("startup")
async def startup():
    await init_db()
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            logger.warning(f"Missing environment variable: {var}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "bot_runner:app",
        host=SERVER_HOST,
        port=SERVER_PORT + 1,
        reload=True,
    )
