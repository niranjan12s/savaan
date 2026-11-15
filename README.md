# Savaan - Experimental Emotionally Aware AI

Savaan is an experimental AI voice assistant project exploring the concept of emotional continuity in human-AI interactions. Rather than treating each conversation as an isolated event, Savaan tracks two continuous emotional variables (**Dopamine** and **Survival**) to shape its responses and context recall over time.

## Core Concept: Emotionally-Driven Memory

Most AI assistants fetch past context using purely semantic similarity (e.g., matching keywords or topics). Savaan experiments with a different approach: **Emotionally-Driven Memory Retrieval**.

Savaan recalls past interactions not just based on *what* you said, but *how the AI and the user felt* at the time. By creating a continuous emotional state, the AI simulates having a "mood," and its retrieval of long-term memory is influenced by the current emotional signature (high dopamine vs. low survival, etc.).

## Multi-Tiered Memory Architecture

Savaan handles context through a dual-layer memory system:

### 1. Short-Term Memory (SQL Database)
Acts as the AI's "working memory" during an active conversation.
* **Storage**: SQLite via SQLModel.
* **Mechanism**: Stores the immediate back-and-forth of the current conversational episode.
* **Lifecycle**: When the AI detects a drop in conversational "continuity" (i.e., a change in topic, tone, or a long pause), the current short-term memory is flushed and processed into long-term memory.

### 2. Long-Term Episodic Memory (Vector Database)
Acts as the AI's "autobiographical memory."
* **Storage**: ChromaDB.
* **Mechanism**: When an episode ends, the AI condenses the short-term memory into exactly six "frames" (key moments) and extracts emotional tone tags. It generates a rich, narrative paragraph describing the emotional journey of that episode.
* **Retrieval**: This narrative is embedded and stored. When a new conversation begins, Savaan probes ChromaDB not with the raw user text, but with a generated *emotional signature* based on the current dopamine/survival metrics and detected tone tags. This fetches past episodes with similar emotional weight.

## User Flow

1. **Input**: User speaks or types a message via the React frontend.
2. **Transcription**: If audio, the FastAPI backend uses Whisper to transcribe it to text.
3. **Emotional Tagging**: The input is analyzed by the Emotion Engine (Gemini) to extract emotional tags and adjust the Dopamine/Survival levels of the user and AI.
4. **Memory Probing**: The new emotional signature is used to query the Vector DB for past episodic memories.
5. **Generation**: The Response Generator uses the current Short-Term Memory, the retrieved Long-Term Episodic Memories, and the current Dopamine/Survival metrics to craft a response.
6. **Continuity Check**: The generator outputs a "continuity score". If the conversation has shifted drastically, the Short-Term Memory is condensed into a new Long-Term Episode and cleared.
7. **Output**: The generated response is returned to the user.



## Tech Stack Overview

* **Frontend**: React 19, Vite, Tailwind CSS v4, Axios.
* **Backend**: Python, FastAPI.
* **Databases**: SQLite (SQLModel) for users and short-term logs, ChromaDB for vector-based episodic memory.
* **AI & ML**: Google Generative AI (`gemini-2.0-flash`) for cognition and emotional tagging, `whisper` for transcription, `sentence-transformers` for embeddings.
## Setup and Run

### Backend (`savaan-service`)

```bash
cd savaan-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `savaan-service/`:

```
API_KEY=<your Google AI Studio key>
SECRET_KEY=<any long random string>
ALLOWED_ORIGINS=http://localhost:5173
```

Run the API from inside `savaan-service/`:

```bash
uvicorn main:app --reload
```

The first run downloads the Whisper `base` model and the `all-MiniLM-L6-v2` embedding model automatically.

### Frontend (`savaan-frontend/voice-ai-frontend`)

```bash
cd savaan-frontend/voice-ai-frontend
npm install
```

Create a `.env` file with the backend URL:

```
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
```

Register a user, log in, and start talking. Watch the dopamine/survival metrics shift between messages.

## Deploy to Cloudflare (optional)

The Worker in `worker/` runs the same pipeline on Cloudflare: Workers AI
(Llama 3.3 for conversation and tagging, Whisper for voice input), Vectorize
for episodic memory, D1 for conversation history, and a Durable Object per
user for the dopamine/survival state.

Prerequisites: a Cloudflare account (free is enough) and
`npx wrangler login`.

```bash
cd worker
npm install
npx wrangler d1 create savaan-db
# paste the printed database_id into wrangler.toml (REPLACE_WITH_D1_ID)
npx wrangler vectorize create episodic-memory --dimensions=768 --metric=cosine
npx wrangler d1 execute savaan-db --file=./schema.sql
npx wrangler deploy
```

Then point the frontend at the Worker by setting `VITE_API_URL` in
`savaan-frontend/voice-ai-frontend/.env`:

```
VITE_API_URL=https://savaan.<your-subdomain>.workers.dev
```

Notes on the Worker version:
- No auth layer: the demo addresses one user id directly
  (`POST /users/<id>/respond`, multipart `file` field with the audio).
- The Python service is unchanged; `SAVAAN_STACK=local` remains the default
  and behaves exactly as before.
- See PROMPTS.md for the prompt history.
