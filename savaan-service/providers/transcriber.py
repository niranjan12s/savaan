"""Transcriber interface and adapters for voice input.

- LocalWhisperTranscriber: openai-whisper running in-process (the original stack).
A Workers AI Whisper adapter lands with the Cloudflare adapter PR.
"""

from abc import ABC, abstractmethod


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Transcribe an audio file, returning the text."""


class LocalWhisperTranscriber(Transcriber):
    def __init__(self, model_size: str = "base"):
        import whisper

        self._model = whisper.load_model(model_size)

    def transcribe(self, audio_path: str) -> str:
        return self._model.transcribe(audio_path)["text"]
