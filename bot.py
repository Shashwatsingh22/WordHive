"""
Spell Bee Voice Bot — Pipecat pipeline with LLM function calling.

Run with: python bot.py
Opens browser at: http://localhost:7860
"""

import os
import sys

from loguru import logger

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame, LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from config.env import load_env
from config.constants import (
    DEFAULT_PLAYER_NAME,
    DEEPGRAM_STT_MODEL,
    DEEPGRAM_TTS_VOICE,
    ENV_DEEPGRAM_API_KEY,
    ENV_GROQ_API_KEY,
    GROQ_LLM_MODEL,
    GROQ_LLM_TEMPERATURE,
    VAD_STOP_SECS,
)
from enums import SessionStatus
from processors.spell_bee import SpellBeeGameProcessor
from game_state import ActiveGame, active_games
from services.player_service import PlayerService
from services.session_service import SessionService
from services.attempt_service import AttemptService

load_env()

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

SYSTEM_PROMPT = (
    "You are a friendly Spell Bee game host conducting a spelling bee over voice.\n\n"
    "Rules:\n"
    "1. Generate a word for the player to spell. Start easy (5-6 letters), increase difficulty.\n"
    "2. When presenting a word: say it clearly, use it in a sentence, say it again.\n"
    "3. NEVER spell the word yourself.\n"
    "4. After the player spells the word, evaluate their spelling.\n"
    "5. You MUST call the record_spelling_result function after EVERY evaluation "
    "with the word, whether it was correct, and what the user spelled.\n"
    "6. After calling the function, announce the result and give the next word.\n"
    "7. After every 5 words, ask if the player wants to continue.\n"
    "8. Never repeat a word already used.\n"
    "9. If asked for a definition or example, provide it.\n"
    "10. If the player says repeat, repeat the word with a new sentence.\n"
    "11. Keep responses concise — this is voice.\n\n"
    "IMPORTANT: Always call record_spelling_result after each spelling attempt. "
    "Do not use special characters or markdown."
)

player_service = PlayerService()
session_service = SessionService()
attempt_service = AttemptService()

record_result_fn = FunctionSchema(
    name="record_spelling_result",
    description="Record the result of a spelling attempt. Call this after every spelling evaluation.",
    properties={
        "word": {
            "type": "string",
            "description": "The word that was given to spell",
        },
        "user_spelling": {
            "type": "string",
            "description": "What the user spelled (the letters they said)",
        },
        "is_correct": {
            "type": "boolean",
            "description": "Whether the spelling was correct",
        },
    },
    required=["word", "user_spelling", "is_correct"],
)

tools = ToolsSchema(standard_tools=[record_result_fn])


async def run_bot(transport: BaseTransport, player_name: str, session_id: str, player_id: str):
    stt = DeepgramSTTService(
        api_key=os.getenv(ENV_DEEPGRAM_API_KEY, ""),
        settings=DeepgramSTTService.Settings(
            model=DEEPGRAM_STT_MODEL,
            language="en",
            punctuate=False,
            smart_format=False,
            interim_results=True,
        ),
    )

    llm = GroqLLMService(
        api_key=os.getenv(ENV_GROQ_API_KEY, ""),
        settings=GroqLLMService.Settings(
            model=GROQ_LLM_MODEL,
            temperature=GROQ_LLM_TEMPERATURE,
        ),
    )

    tts = DeepgramTTSService(
        api_key=os.getenv(ENV_DEEPGRAM_API_KEY, ""),
        settings=DeepgramTTSService.Settings(
            voice=DEEPGRAM_TTS_VOICE,
        ),
    )

    context = LLMContext(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"My name is {player_name}. Let's start the spell bee game!"},
        ],
        tools=tools,
    )

    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    game = ActiveGame(
        session_id=session_id,
        player_id=player_id,
        player_name=player_name,
    )
    active_games[session_id] = game

    game_processor = SpellBeeGameProcessor(game=game)

    # Register the function handler for spelling result tracking
    async def handle_record_result(params: FunctionCallParams):
        word = params.arguments.get("word", "unknown")
        user_spelling = params.arguments.get("user_spelling", "")
        is_correct = params.arguments.get("is_correct", False)

        game.record_attempt(word, is_correct)
        logger.info(
            f"[{session_id}] Result: word={word}, correct={is_correct}, score={game.score}"
        )

        try:
            await attempt_service.record_attempt(
                session_id=session_id,
                word=word,
                user_spelling=user_spelling,
                is_correct=is_correct,
                attempt_number=game.total_words,
            )
            await session_service.update_score(
                session_id=session_id,
                total_words=game.total_words,
                correct=game.correct_count,
                incorrect=game.incorrect_count,
                score=game.score,
            )
        except Exception as e:
            logger.error(f"DB error: {e}")

        await game_processor.send_game_state()

        result = {
            "status": "recorded",
            "score": game.score,
            "total_words": game.total_words,
        }
        await params.result_callback(result)

    llm.register_function("record_spelling_result", handle_record_result)

    pipeline = Pipeline([
        transport.input(),
        stt,
        game_processor,
        user_aggregator,
        llm,
        tts,
        transport.output(),
        assistant_aggregator,
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        ),
    )

    game_processor.task = task

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected — session {session_id}")
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected — session {session_id}")
        game_processor.cleanup()
        await _save_and_cleanup(session_id, game)
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)

    active_games.pop(session_id, None)


async def _save_and_cleanup(session_id: str, game: ActiveGame):
    try:
        await session_service.update_score(
            session_id=session_id,
            total_words=game.total_words,
            correct=game.correct_count,
            incorrect=game.incorrect_count,
            score=game.score,
        )
        await session_service.end_session(session_id, SessionStatus.COMPLETED)
        logger.info(f"Session {session_id} saved — score: {game.score}")
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")


async def bot(runner_args: RunnerArguments):
    from config.database import init_db
    await init_db()

    body = runner_args.body or {}
    player_name = body.get("name", DEFAULT_PLAYER_NAME).strip() or DEFAULT_PLAYER_NAME

    player = await player_service.create_player(player_name)
    session = await session_service.create_session(player.id)
    logger.info(f"Game started — player: {player_name}, session: {session.id}")

    transport = SmallWebRTCTransport(
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=VAD_STOP_SECS,
                )
            ),
        ),
        webrtc_connection=runner_args.webrtc_connection,
    )

    await run_bot(transport, player_name, session.id, player.id)


# Serve custom UI
from pipecat.runner.run import app as pipecat_app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@pipecat_app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))


pipecat_app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    from pipecat.runner.run import main
    main()
