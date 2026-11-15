# PROMPTS.md

Prompt history for Savaan's Cloudflare port: the LLM prompts the app runs with,
and how AI assistance was used to build the port.

## Application prompts

All prompts are defined in `worker/src/prompts.ts` (ported verbatim from the
original Python service; sources noted per function).

1. **Emotion tagging** (`buildEmotionTaggingPrompt`) - scores a conversation
   segment against the 30-tag stimuli taxonomy (`stimuli_tags.yaml`) with
   weights in [-1, 1]. Runs on the user's transcript and on Savaan's reply;
   the resulting tag scores drive the dopamine/survival state update.
2. **Reply generation** (`buildReplyPrompt`) - the core persona prompt: Savaan
   responds from its own simulated dopamine/survival state, with current
   metrics, temporal history, full conversation, and retrieved episodic
   memories injected. Returns `{response, continuity}` JSON.
3. **Episodic memory creation** (`buildEpisodicMemoryPrompt`) - condenses a
   conversation into six frames plus distinct emotion tags when continuity
   breaks.
4. **Episode embedding summary** (`buildEpisodicEmbeddingPrompt`) - turns the
   episode's metric history and tags into one rich paragraph, which is then
   embedded and stored in Vectorize.
5. **Recall probe** (`buildEpisodeProbePrompt`) - describes the current
   moment's emotional signature in vivid language (never raw numbers) to query
   episodic memory semantically.

All JSON-returning prompts strip markdown fences before parsing
(`parseJsonResponse`).

## Models

- Conversation and tagging: Workers AI `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- Voice input: Workers AI `@cf/openai/whisper-large-v3-turbo`
- Memory embeddings: Workers AI `@cf/baai/bge-base-en-v1.5` (768-dim, cosine)

## Build process

The Cloudflare port (provider interfaces in the Python service, the Worker,
Durable Object emotion state, D1/Vectorize adapters, and this file) was
developed with AI assistance (Instinct). Iteration went: (1) read the original
FastAPI service and map each external dependency to a port; (2) introduce
provider interfaces behind a `SAVAAN_STACK` switch with zero behavior change;
(3) implement the Cloudflare adapters as a Worker with the prompts ported
verbatim; (4) type-check the Worker and smoke-test the Python pipeline. All
generated code was reviewed before committing, and every PR is reviewed by the
repo owner before merge.
