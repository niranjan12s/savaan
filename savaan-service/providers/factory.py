"""Provider selection.

SAVAAN_STACK picks a whole preset; the individual *_PROVIDER variables override
one provider at a time. Defaults reproduce the original local stack exactly, so
with no environment changes the app behaves byte-for-byte as before.
"""

import os

from providers.llm import GeminiLLM, LLMProvider
from providers.state_store import SQLiteStateStore, StateStore
from providers.transcriber import LocalWhisperTranscriber, Transcriber
from providers.vector_store import ChromaVectorStore, VectorStore

_PRESETS = {
    "local": {
        "llm": "gemini",
        "vector_store": "chroma",
        "state_store": "sqlite",
        "transcriber": "local_whisper",
    },
}


def _pick(kind: str) -> str:
    stack = os.getenv("SAVAAN_STACK", "local")
    if stack not in _PRESETS:
        raise ValueError(f"Unknown SAVAAN_STACK '{stack}'. Known stacks: {sorted(_PRESETS)}")
    return os.getenv(f"{kind.upper()}_PROVIDER", _PRESETS[stack][kind])


def get_llm() -> LLMProvider:
    name = _pick("llm")
    if name == "gemini":
        return GeminiLLM()
    raise ValueError(f"Unknown LLM provider '{name}'")


def get_vector_store() -> VectorStore:
    name = _pick("vector_store")
    if name == "chroma":
        return ChromaVectorStore()
    raise ValueError(f"Unknown vector store provider '{name}'")


def get_state_store() -> StateStore:
    name = _pick("state_store")
    if name == "sqlite":
        return SQLiteStateStore()
    raise ValueError(f"Unknown state store provider '{name}'")


def get_transcriber() -> Transcriber:
    name = _pick("transcriber")
    if name == "local_whisper":
        return LocalWhisperTranscriber()
    raise ValueError(f"Unknown transcriber provider '{name}'")
