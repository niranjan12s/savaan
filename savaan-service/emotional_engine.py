import os
import yaml
from pathlib import Path

from dotenv import load_dotenv

from providers.llm import LLMProvider, parse_json_response

load_dotenv()


def load_stimuli_tags(path=None):
    if path is None:
        path = Path(__file__).parent / "stimuli_tags.yaml" 
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return [item['tag'] for item in data['stimuli_tags']]


def build_emotion_tagging_prompt(input, tag_list):
    tags_string = ', '.join(tag_list)

    prompt = f"""
You are an emotional inference engine that analyzes a piece of human conversation and assigns intensity scores to emotional state tags that are present.

Here are the allowed emotional state tags:
{tags_string}

Conversation segment to analyze:
"{input}"

Each tone tag affects dopmaine and survival differently, low dopamine leads to a sadder user and low survival indicates more desperation, more drastic

Your task is to output a JSON object mapping each **relevant** tag to a number between **-1.0 and 1.0**, representing the **strength and direction** of that emotion:

- Positive values (e.g. 0.8) indicate strong presence.
- Negative values (e.g. -0.7) indicate emotional suppression or inverse expression.
- 0 means emotional neutrality or irrelevance.
- Always Include all tags with relevant values to them based on their presence.
- If no meaningful emotional signals are present, return an empty object.

Format your output as:

```json
{{
  "tag1": score,
  "tag2": score,
  ...
}}
Do not generate any text apart from the json
"""
    return prompt

def generate_emotional_summary(input, llm: LLMProvider):
    try:
        response = llm.generate(build_emotion_tagging_prompt(
            input,load_stimuli_tags()
))
        return parse_json_response(response)
    except Exception as e:
        print(f"Error occurred during tag generation: {e}")
        return None
    