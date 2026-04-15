# 🐝 WordHive — Spell Bee Voice Bot

A voice-based Spell Bee game built with **Pipecat** framework. The bot conducts a spelling bee over a live voice call — it speaks a word, the user spells it out loud, and the bot evaluates the response in real-time.

## Architecture

```
┌──────────────────────┐     WebRTC (SmallWebRTC)    ┌─────────────────────┐
│  Frontend            │ ◄──────────────────────────► │  Pipecat Server     │
│  (HTML/CSS/JS)       │                              │  (Python)           │
└──────────────────────┘                              └────────┬────────────┘
                                                               │
                                                ┌──────────────┼──────────────┐
                                                ▼              ▼              ▼
                                          Deepgram STT   Deepgram TTS    Groq LLM
                                                               │
                                                          ┌────▼─────┐
                                                          │  SQLite  │
                                                          └──────────┘
```

## Tech Stack

| Layer       | Technology                  | Why                                                    |
|-------------|-----------------------------|---------------------------------------------------------|
| Voice       | Pipecat (Python)            | Real-time voice pipeline framework (project requirement)|
| Transport   | SmallWebRTCTransport        | Built-in Pipecat transport, no external service needed  |
| STT         | Deepgram                    | Real-time streaming speech-to-text, free tier available |
| TTS         | Deepgram                    | Low-latency text-to-speech, same provider as STT        |
| LLM         | Groq (Llama 3.3 70B)       | Free tier, ultra-fast inference for real-time voice      |
| Backend     | Pipecat Runner + FastAPI    | Built-in dev server + optional REST API endpoints       |
| Frontend    | HTML + CSS + Vanilla JS     | Simple, no build step, raw WebRTC connection            |
| Database    | SQLite (aiosqlite)          | Zero setup, sufficient for this scope                   |

## How It Works

1. User opens the web UI → enters name → clicks "Start Game"
2. Frontend creates a WebRTC peer connection and sends an SDP offer to `/api/offer`
3. Pipecat spawns a new bot instance with its own pipeline and returns an SDP answer — live audio connection established
4. **Game loop (all via voice):**
   - Bot generates a word using LLM → TTS speaks it to the user
   - User spells the word out loud → STT transcribes in real-time
   - LLM evaluates the spelling and calls `record_spelling_result` function to record the result
   - Bot responds with correct/incorrect → moves to next word
5. Game state (score, words) pushed to frontend in real-time via WebRTC data channel

## Key Features

- **Dynamic word generation** — LLM generates words (no hardcoded list), with progressive difficulty
- **LLM function calling** — Spelling evaluation and score tracking via Groq LLM tool calls (`record_spelling_result`)
- **Real-time voice interaction** — WebRTC audio streaming with sub-second latency
- **Turn-taking** — VAD (Voice Activity Detection) with 1.5s silence threshold for spelling pauses
- **Interruption handling** — User can interrupt the bot mid-speech cleanly
- **Custom frame processor** — Pipecat processor for game state tracking, idle timeout, and live UI updates
- **Live game state** — Score, correct/incorrect counts pushed to frontend via WebRTC data channel
- **Persistent storage** — Game sessions and word attempts saved to SQLite
- **Idle timeout** — Auto-reminds inactive players, ends game after 3 unanswered prompts (2 min each)

## Project Structure

```
WordHive/
├── api/
│   └── game_routes.py          # REST API endpoints (game state, leaderboard)
├── config/
│   ├── constants.py            # All env keys, service configs, defaults
│   ├── database.py             # SQLite connection + migration runner
│   └── env.py                  # Environment file loader (.env support)
├── enums/
│   ├── session_status.py       # SessionStatus enum
│   └── type_group.py           # TypeGroup enum
├── migration_files/            # Flyway-style versioned SQL scripts
│   ├── V1__create_type_system.sql
│   ├── V2__create_players.sql
│   ├── V3__create_sessions.sql
│   ├── V4__create_word_attempts.sql
│   └── V5__seed_session_statuses.sql
├── models/                     # Pure dataclass models
│   ├── base.py
│   ├── player.py
│   ├── session.py
│   ├── type.py
│   ├── type_group.py
│   └── word_attempt.py
├── processors/
│   └── spell_bee.py            # Custom Pipecat frame processor
├── services/                   # Business logic + DB operations
│   ├── player_service.py
│   ├── session_service.py
│   └── attempt_service.py
├── sql/                        # Runtime SQL query files
│   ├── player_queries.sql
│   ├── session_queries.sql
│   └── attempt_queries.sql
├── static/                     # Frontend UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── bot.py                      # Pipecat pipeline — main entry point
├── bot_runner.py               # Optional FastAPI server for API endpoints
├── game_state.py               # In-memory game state tracker
├── .env.example
├── requirements.txt
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10+
- API keys for:
  - [Deepgram](https://console.deepgram.com/) — STT & TTS (free credits)
  - [Groq](https://console.groq.com/) — LLM inference (free tier)

## Setup & Run

```bash
# Clone the repo
git clone https://github.com/Shashwatsingh22/WordHive.git
cd WordHive

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the bot
python bot.py
```

Open `http://localhost:7860` in your browser to play.

## Environment Variables

```
DEEPGRAM_API_KEY=your_deepgram_api_key
GROQ_API_KEY=your_groq_api_key
```

## Deploy to Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → "New Project" → "Deploy from GitHub repo"
3. Select your repo — Railway auto-detects the config from `nixpacks.toml`
4. Add environment variables in the Railway dashboard:
   - `DEEPGRAM_API_KEY`
   - `GROQ_API_KEY`
5. Railway auto-deploys on every push to `main`

Railway assigns a `PORT` env var automatically — the `nixpacks.toml` and `Procfile` handle passing it to the Pipecat runner.

## License

MIT
