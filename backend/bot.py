"""
Spell Bee Voice Bot — Pipecat pipeline definition.

Creates the voice pipeline and runs it for a single game session.
Spawned as a subprocess by bot_runner.py.
"""

import argparse
import asyncio
import os
import sys

import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import (
    LLMContext,
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.groq import GroqLLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport

from enums import SessionStatus
from config.constants import (
    BOT_DISPLAY_NAME,
    DEFAULT_PLAYER_NAME,
    DEEPGRAM_STT_MODEL,
    DEEPGRAM_TTS_VOICE,
    ENV_DAILY_API_KEY,
    ENV_DEEPGRAM_API_KEY,
    ENV_GROQ_API_KEY,
    GROQ_LLM_MODEL,
    GROQ_LLM_TEMPERATURE,
    VAD_STOP_SECS,
)
from game_state import ActiveGame, active_games
from processors.spell_bee import SpellBeeGameProcessor
from services.session_service import SessionService
from services.attempt_service import AttemptService

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

SYSTEM_PROMPT = (
    "You are a friendly Spell Bee game host conducting a spelling bee over voice.\n\n"
    "Rules:\n"
    "1. Generate a word for the player to spell. Start with easy words (5-6 letters), "
    "and gradually increase difficulty as the player gets words correct.\n"
    "2. When presenting a word, ALWAYS follow this format: say the word clearly, "
    "use it in a sentence, then say the word again. "
    'Example: "Your word is BEAUTIFUL. The sunset was beautiful tonight. BEAUTIFUL. '
    'Please spell it."\n'
    "3. NEVER spell the word yourself. The player must spell it.\n"
    "4. After the player spells the word, evaluate their spelling. "
    "If correct: congratulate them, announce the score, and give the next word. "
    'If incorrect: say "That\'s incorrect. The correct spelling is..." then spell it out, '
    "announce the score, and give the next word.\n"
    "5. Keep track of the score: +10 points for each correct answer.\n"
    "6. After every 5 words, ask if the player wants to continue or end the game.\n"
    "7. Never repeat a word you have already used in this session.\n"
    "8. If the player asks for a definition, example sentence, or language of origin, provide it.\n"
    "9. If the player says repeat or say it again, repeat the current word with a new sentence.\n"
    "10. Keep your responses concise and clear. This is voice, not text.\n"
    "11. When the player wants to end the game, give a summary of their performance.\n\n"
    "IMPORTANT: You are speaking over voice. Do not use special characters, markdown, or formatting. "
    "Keep sentences short and natural for speech."
)

session_service = SessionService()
attempt_service = AttemptService()


async def run_bot(room_url: str, token: str, session_id: str,
                  player_id: str, player_name: str):

    async with aiohttp.ClientSession() as session:
        transport = DailyTransport(
            room_url,
            token,
            BOT_DISPLAY_NAME,
            DailyParams(
                api_key=os.getenv(ENV_DAILY_API_KEY, ""),
                audio_in_enabled=True,
                audio_out_enabled=True,
                video_out_enabled=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(
                    params=SileroVADAnalyzer.VADParams(
                        stop_secs=VAD_STOP_SECS,
                    )
                ),
            ),
        )

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
                {
                    "role": "user",
                    "content": f"My name is {player_name}. Let's start the spell bee game!",
                },
            ]
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

        game_processor = SpellBeeGameProcessor(game=game, transport=transport)

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

        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            logger.info(f"Participant joined: {participant['id']}")
            await task.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"Participant left: {participant['id']}, reason: {reason}")
            await _save_and_cleanup(session_id, game, SessionStatus.COMPLETED)
            await task.queue_frame(EndFrame())

        @transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            if state == "left":
                await task.queue_frame(EndFrame())

        runner = PipelineRunner()
        await runner.run(task)

    active_games.pop(session_id, None)
    logger.info(f"Bot session {session_id} ended.")


async def _save_and_cleanup(session_id: str, game: ActiveGame, status: SessionStatus):
    try:
        await session_service.update_score(
            session_id=session_id,
            total_words=game.total_words,
            correct=game.correct_count,
            incorrect=game.incorrect_count,
            score=game.score,
        )
        await session_service.end_session(session_id, status)
        logger.info(f"Session {session_id} saved to DB with status {status.name}")
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WordHive Spell Bee Bot")
    parser.add_argument("-u", "--url", type=str, required=True, help="Daily room URL")
    parser.add_argument("-t", "--token", type=str, required=True, help="Daily token")
    parser.add_argument("-s", "--session-id", type=str, required=True, help="Game session ID")
    parser.add_argument("-p", "--player-id", type=str, required=True, help="Player ID")
    parser.add_argument("-n", "--player-name", type=str, default=DEFAULT_PLAYER_NAME, help="Player name")
    config = parser.parse_args()

    asyncio.run(run_bot(config.url, config.token, config.session_id,
                        config.player_id, config.player_name))
