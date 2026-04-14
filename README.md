# 🐝 WordHive — Spell Bee Voice Bot

A voice-based Spell Bee game built with **Pipecat** framework. The bot conducts a spelling bee over a live voice call — it speaks a word, the user spells it out loud, and the bot evaluates the response in real-time.

## Architecture

```
┌──────────────────────┐       WebRTC (Daily)        ┌─────────────────────┐
│  Frontend            │ ◄─────────────────────────► │  Pipecat Server     │
│  (HTML/CSS/JS)       │                             │  (Python)           │
│                      │ ◄─── REST (fetch) ────────► │  FastAPI endpoints  │
└──────────────────────┘                             └────────┬────────────┘
                                                              │
                                              ┌───────────────┼───────────────┐
                                              ▼               ▼               ▼
                                        Deepgram STT    Deepgram TTS     Groq LLM
                                                              │
                                                         ┌────▼─────┐
                                                         │  SQLite  │
                                                         └──────────┘
```

## Tech Stack

| Layer       | Technology                  | Why                                                    |
|-------------|-----------------------------|---------------------------------------------------------|
| Voice       | Pipecat (Python)            | Real-time voice pipeline framework (project requirement)|
| Transport   | Daily (WebRTC)              | Pipecat's native transport for browser audio streaming  |
| STT         | Deepgram                    | Real-time streaming speech-to-text, free tier available |
| TTS         | Deepgram                    | Low-latency text-to-speech, same provider as STT        |
| LLM         | Groq (Llama 3.3 70B)       | Free tier, ultra-fast inference for real-time voice      |
| Backend     | FastAPI                     | Serves REST API + spawns Pipecat bot processes          |
| Frontend    | HTML + CSS + Vanilla JS     | Simple, no build step, uses Daily JS SDK for WebRTC     |
| Database    | SQLite (SQLAlchemy async)   | Zero setup, sufficient for this scope                   |

## How It Works

1. User opens the web UI → enters name → clicks "Start Game"
2. Backend creates a Daily WebRTC room and spawns a Pipecat bot process
3. Frontend joins the room via Daily JS SDK — live audio connection established
4. **Game loop (all via voice):**
   - Bot generates a word using LLM → TTS speaks it to the user
   - User spells the word out loud → STT transcribes in real-time
   - Custom frame processor validates the spelling
   - Bot responds with correct/incorrect → moves to next word
5. Game state (score, words) displayed on frontend in real-time

## Key Features

- **Dynamic word generation** — LLM generates words (no hardcoded list), with progressive difficulty
- **Real-time voice interaction** — WebRTC audio streaming with sub-second latency
- **Turn-taking** — VAD (Voice Activity Detection) with 1.5s silence threshold for spelling pauses
- **Interruption handling** — User can interrupt the bot mid-speech cleanly
- **Custom frame processor** — Pipecat processor for game state tracking and spelling validation
- **Live game state** — Score, correct/incorrect counts pushed to frontend via Daily app messages
- **Persistent storage** — Game sessions and word attempts saved to SQLite

## Project Structure

```
WordHive/
├── backend/
│   ├── bot.py              # Pipecat pipeline — voice bot logic
│   ├── bot_runner.py       # FastAPI server — REST API + bot spawner
│   ├── processors.py       # Custom Pipecat frame processors
│   ├── game_state.py       # In-memory game state tracker
│   ├── database.py         # SQLAlchemy async DB setup
│   ├── models.py           # DB models (Player, GameSession, WordAttempt)
│   ├── .env.example        # Environment variables template
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Single-page game UI
│   ├── style.css           # Styling
│   └── app.js              # Daily JS SDK + game logic
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10+
- API keys for:
  - [Daily](https://dashboard.daily.co/) — WebRTC transport (free tier)
  - [Deepgram](https://console.deepgram.com/) — STT & TTS (free credits)
  - [Groq](https://console.groq.com/) — LLM inference (free tier)

## Setup & Run

```bash
# Clone the repo
git clone <repo-url>
cd WordHive

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Run the server
cd backend
python bot_runner.py
```

Open `http://localhost:7860` in your browser to play.

## Environment Variables

```
DAILY_API_KEY=your_daily_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
GROQ_API_KEY=your_groq_api_key
```

## License

MIT
