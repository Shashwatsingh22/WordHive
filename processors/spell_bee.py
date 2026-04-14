"""
SpellBeeGameProcessor — custom Pipecat frame processor.

Tracks game state, sends live updates to frontend, handles idle timeout.
Spelling evaluation is handled via LLM function calling (see bot.py).
"""

import asyncio

from loguru import logger

from pipecat.frames.frames import Frame, OutputTransportMessageFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from game_state import ActiveGame
from services.session_service import SessionService
from enums import SessionStatus

IDLE_TIMEOUT_SECS = 120
MAX_IDLE_REMINDERS = 3

session_service = SessionService()


class SpellBeeGameProcessor(FrameProcessor):

    def __init__(self, game: ActiveGame, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.task = None
        self._idle_timer = None
        self._idle_count = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            self._idle_count = 0
            self._reset_idle_timer()
            logger.info(f"[{self.game.session_id}] User: {frame.text}")

        await self.push_frame(frame, direction)

    async def send_game_state(self):
        try:
            msg = OutputTransportMessageFrame(self.game.to_dict())
            if self.task:
                logger.info(f"[{self.game.session_id}] Sending game state via task: {self.game.to_dict()}")
                await self.task.queue_frame(msg)
            else:
                await self.push_frame(msg, FrameDirection.DOWNSTREAM)
        except Exception as e:
            logger.error(f"Failed to send game state: {e}")

    def _reset_idle_timer(self):
        if self._idle_timer:
            self._idle_timer.cancel()
        loop = asyncio.get_event_loop()
        self._idle_timer = loop.call_later(
            IDLE_TIMEOUT_SECS, lambda: asyncio.ensure_future(self._on_idle())
        )

    async def _on_idle(self):
        self._idle_count += 1
        logger.info(f"[{self.game.session_id}] Idle timeout #{self._idle_count}")

        if self._idle_count >= MAX_IDLE_REMINDERS:
            logger.info(f"[{self.game.session_id}] Max idle — ending game")
            try:
                await session_service.update_score(
                    session_id=self.game.session_id,
                    total_words=self.game.total_words,
                    correct=self.game.correct_count,
                    incorrect=self.game.incorrect_count,
                    score=self.game.score,
                )
                await session_service.end_session(
                    self.game.session_id, SessionStatus.ABANDONED
                )
            except Exception as e:
                logger.error(f"DB error on idle end: {e}")

            state = self.game.to_dict()
            state["game_over"] = True
            state["reason"] = "idle_timeout"
            try:
                msg = OutputTransportMessageFrame(state)
                if self.task:
                    await self.task.queue_frame(msg)
                else:
                    await self.push_frame(msg, FrameDirection.DOWNSTREAM)
            except Exception:
                pass
            return

        if self.task:
            from pipecat.frames.frames import LLMMessagesAppendFrame
            reminder = {
                "role": "user",
                "content": "I haven't heard anything. Are you still there? Please spell the word.",
            }
            await self.task.queue_frames(
                [LLMMessagesAppendFrame([reminder], run_llm=True)]
            )
        self._reset_idle_timer()

    def cleanup(self):
        if self._idle_timer:
            self._idle_timer.cancel()
            self._idle_timer = None
