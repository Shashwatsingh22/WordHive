"""
Game API routes.

POST /api/start-game
GET  /api/game-state/{session_id}
GET  /api/leaderboard
"""

import os
import subprocess

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger

from api.daily_helpers import create_daily_room, get_daily_token
from config.constants import DEFAULT_PLAYER_NAME
from game_state import active_games
from services.player_service import PlayerService
from services.session_service import SessionService

router = APIRouter(prefix="/api")

player_service = PlayerService()
session_service = SessionService()


@router.post("/start-game")
async def start_game(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        player_name = data.get("name", DEFAULT_PLAYER_NAME).strip() or DEFAULT_PLAYER_NAME
    except Exception:
        player_name = DEFAULT_PLAYER_NAME

    player = await player_service.create_player(player_name)
    session = await session_service.create_session(player.id)

    try:
        room = await create_daily_room()
        room_url = room["url"]
        room_name = room["name"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create room: {e}")

    try:
        bot_token = await get_daily_token(room_name)
        user_token = await get_daily_token(room_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tokens: {e}")

    try:
        subprocess.Popen(
            [
                "python3", "bot.py",
                "-u", room_url,
                "-t", bot_token,
                "-s", session.id,
                "-p", player.id,
                "-n", player_name,
            ],
            cwd=os.path.dirname(os.path.abspath(__file__)) + "/..",
        )
        logger.info(f"Bot spawned for session {session.id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {e}")

    return JSONResponse({
        "room_url": room_url,
        "token": user_token,
        "session_id": session.id,
        "player_name": player_name,
    })


@router.get("/game-state/{session_id}")
async def get_game_state(session_id: str) -> JSONResponse:
    game = active_games.get(session_id)
    if game:
        return JSONResponse(game.to_dict())

    session = await session_service.get_session(session_id)
    if session:
        return JSONResponse({
            "session_id": session.id,
            "score": session.score,
            "correct_count": session.correct_count,
            "incorrect_count": session.incorrect_count,
            "total_words": session.total_words,
            "status_id": session.status_id,
        })

    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/leaderboard")
async def get_leaderboard() -> JSONResponse:
    results = await session_service.get_leaderboard()
    return JSONResponse(results)
