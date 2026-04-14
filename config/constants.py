"""
Application-wide constants for WordHive.

All environment variable keys, default values, service configs,
and magic strings live here.
"""

# --- Environment Variable Keys ---

ENV_DEEPGRAM_API_KEY = "DEEPGRAM_API_KEY"
ENV_GROQ_API_KEY = "GROQ_API_KEY"
ENV_DATABASE_PATH = "DATABASE_PATH"

REQUIRED_ENV_VARS = [ENV_DEEPGRAM_API_KEY, ENV_GROQ_API_KEY]

# --- Default Values ---

DEFAULT_DATABASE_PATH = "spellbee.db"
DEFAULT_PLAYER_NAME = "Player"

# --- Service Configuration ---

DEEPGRAM_STT_MODEL = "nova-3-general"
DEEPGRAM_TTS_VOICE = "aura-2-helena-en"
GROQ_LLM_MODEL = "llama-3.3-70b-versatile"
GROQ_LLM_TEMPERATURE = 0.7
VAD_STOP_SECS = 1.5

# --- Server ---

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 7860

# --- Game ---

SCORE_PER_CORRECT = 10
