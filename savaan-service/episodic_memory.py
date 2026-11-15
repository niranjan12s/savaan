import json
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

from providers.llm import LLMProvider, parse_json_response
from providers.state_store import StateStore
from providers.vector_store import VectorStore

def create_episodic_memory(user_id,state_store: StateStore,llm: LLMProvider):
        conversation=state_store.get_conversation_history(user_id)
        prompt = f"""
You are responsible for generating an episodic memory from the conversation between a user and an AI.

Step 1: Condense the entire conversation into exactly six *distinct* and *non-redundant* lines (called frames), each line capturing a unique and important detail from the interaction. These may include emotional highs or lows, key phrases, decisions, philosophical insights, or notable shifts in tone or topic. Ensure a balanced representation of both user and AI in these six lines.

Step 2: Identify and list all emotional tone tags (feelings, moods, or mental states) exhibited across the conversation by both the user and the AI. Avoid duplicate or overly similar emotional labels. Only include distinct emotional impressions.

Input Conversation:
{json.dumps(conversation)}

Return the output strictly in the following JSON format:
```json
{{
  "frames": [
    "First line summarizing key moment...",
    "Second unique insight...",
    "... up to six lines"
  ],
  "tags": [
    "distinct_emotion_1",
    "distinct_emotion_2",
    "... as many as needed"
  ]
}}
Only return a valid json
"""
        return parse_json_response(llm.generate(prompt))

def create_episodic_embedding(user_id,episode_tags,state_store: StateStore,current_metrics,llm: LLMProvider):
    historical_metrics=state_store.get_metrics_history(user_id)
    prompt = f"""
You are an emotional summarizer designed for episodic memory storage. You are given the following data:

1. Dopamine and survival history over an episode (values are normalized between 0 and 1):
   - User dopamine history: {historical_metrics["dopamine_user"]}
   - User survival history: {historical_metrics["survival_user"]}
   - AI dopamine history: {historical_metrics["dopamine_ai"]}
   - AI survival history: {historical_metrics["survival_ai"]}

2. Tone tags detected for this episode: {episode_tags}

3. Current dopamine and survival values:
   - User: dopamine={current_metrics["dopamine_user"]}, survival={current_metrics["survival_user"]}
   - AI: dopamine={current_metrics["dopamine_ai"]}, survival={current_metrics["survival_ai"]}

Notes:
- A value near 1 represents a **high level of dopamine or survival**, a value near 0 represents a **low level**.  
- Trends, spikes, or dips in these values are meaningful and should be described **richly** and contextually.

Your task is to generate a **single, coherent paragraph** that summarizes the emotional journey of this episode. Follow these rules:

- Capture the **trend and dynamics** of dopamine and survival for both the user and AI.  
  - Use expressive descriptions like "a sudden spike," "gradual decline," "emotional tension," "moment of relief," or "plateau in engagement."  
- Incorporate the **tone tags naturally**, reflecting the feelings and context of the conversation.  
- Highlight the **interdependence** of the user and AI emotional states when relevant.  
- Keep the paragraph **rich, descriptive, and concise**, suitable for embedding in a vector database for episodic memory retrieval.  
- Avoid raw lists, numeric data, or overly generic statements; focus on storytelling style that conveys the emotional flow.  

Return **only the paragraph**, ready to be vectorized for memory retrieval.
"""
    return llm.generate(prompt)



def parse_episodic_memory(user_id,state_store: StateStore,vector_store: VectorStore,llm: LLMProvider):
    episodic_memory=create_episodic_memory(user_id,state_store,llm)
    current_metrics=state_store.get_current_metrics(user_id)
    episodic_embedding=create_episodic_embedding(user_id,episodic_memory["tags"],state_store,current_metrics,llm)
    vector_store.add_episode(
          episode_id=str(uuid4()),
          documents=episodic_memory["frames"],
          embedding=vector_store.embed(episodic_embedding),
          metadata={ 
                "user_id":user_id,
                "dopamine_user":current_metrics["dopamine_user"],
                "survival_user":current_metrics["survival_user"],
                "dopamine_ai":current_metrics["dopamine_ai"],
                "survival_ai":current_metrics["survival_ai"],
                "tags":", ".join(episodic_memory["tags"]),
                "episodic_embedding":episodic_embedding,
                "timestamp":datetime.now(timezone.utc).isoformat()
          }
    )

  
def generate_episode_probe_prompt(
    tone_tags: dict,
    snippet: str,
    dopamine_user: float,
    survival_user: float,
    dopamine_ai: float,
    survival_ai: float,
    history_snippet: Optional[str] = None
) -> str:
    tone_description = ", ".join([f"{tag}: {value:.2f}" for tag, value in tone_tags.items() if value > 0.01])

    prompt = f"""
You are a reflective cognition model. Your job is to generate a single rich paragraph that semantically captures the **emotional signature** of the current situation.

Inputs:
- Tone tag probabilities detected in the last exchange: {tone_description}
- Current dopamine and survival values:
Notes:
- A value near 1 represents a **high level of dopamine or survival**, a value near 0 represents a **low level**.
    - User → dopamine={dopamine_user:.2f}, survival={survival_user:.2f}
    - AI   → dopamine={dopamine_ai:.2f}, survival={survival_ai:.2f}
Current Conversation line:
{snippet}

Optional Conversation Snapshot:
{history_snippet if history_snippet else "None provided."}

Instructions:
- Do not state the raw dopamine/survival values.
- Instead, describe what they *mean emotionally* (e.g., sudden spike, flattening, prolonged stress).
- Use emotionally meaningful, vivid language — not just "high" or "low".
- This paragraph will be used to **query past emotional experiences** stored in episodic memory.

Output:
One standalone paragraph describing the emotional and interpersonal nature of this moment.
"""
    return prompt.strip()


def fetch_from_episodic_memory(user_id,snippet,tone_tags,state_store: StateStore,vector_store: VectorStore):
    current_metrics=state_store.get_current_metrics(user_id)
    episodic_probe=generate_episode_probe_prompt(tone_tags,snippet,current_metrics["dopamine_user"],current_metrics["survival_user"],
                                  current_metrics["dopamine_ai"],current_metrics["dopamine_ai"],state_store.get_conversation_history(user_id))

    return vector_store.query_episodes(vector_store.embed(episodic_probe), n_results=5)