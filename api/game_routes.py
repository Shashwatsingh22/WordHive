"""
Game API routes.

GET  /api/game-state/{session_id}
GET  /api/leaderboard
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from game_state import active_games
from services.session_service import SessionService

router = APIRouter(prefix="/api")

session_service = SessionService()


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
