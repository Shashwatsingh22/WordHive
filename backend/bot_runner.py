"""
Bot Runner — FastAPI application entry point.

Initializes database, registers API routes, serves frontend.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config.constants import REQUIRED_ENV_VARS, SERVER_HOST, SERVER_PORT
from config.database import init_db
from api.game_routes import router as game_router

load_dotenv(override=True)

app = FastAPI(title="WordHive — Spell Bee Voice Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)


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
        port=SERVER_PORT,
        reload=True,
    )
