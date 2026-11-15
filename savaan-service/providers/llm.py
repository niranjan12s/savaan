"""LLM provider interface and adapters.

The emotion engine talks only to LLMProvider.generate(). Implementations:
- GeminiLLM: Google Generative AI (the original stack).
A Workers AI implementation lands with the Cloudflare adapter PR.
"""

import json
import os
import re
from abc import ABC, abstractmethod

from dotenv import load_dotenv

load_dotenv()


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send a prompt, return the raw response text."""


class GeminiLLM(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("API_KEY"))
        self._model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        return self._model.generate_content(prompt).text


def parse_json_response(text: str):
    """Strip markdown fences and parse the JSON body of an LLM response."""
    cleaned = re.sub(r"```json|```", "", text).strip()
    return json.loads(cleaned)
