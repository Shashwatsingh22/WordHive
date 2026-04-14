"""
SpellBeeGameProcessor — custom Pipecat frame processor.

Sits in the pipeline after STT, before user_aggregator.
Tracks game state and sends real-time updates to frontend.
"""

from loguru import logger

from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from game_state import ActiveGame


class SpellBeeGameProcessor(FrameProcessor):

    def __init__(self, game: ActiveGame, transport, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.transport = transport

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            logger.info(f"[{self.game.session_id}] User said: {frame.text}")
            await self._send_game_state()

        await self.push_frame(frame, direction)

    async def _send_game_state(self):
        try:
            await self.transport.send_app_message(self.game.to_dict())
        except Exception as e:
            logger.error(f"Failed to send game state: {e}")
