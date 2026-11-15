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

## Development prompt history

The Cloudflare port, deployment, and debugging (Nov 15-16, 2026) were directed
by the repo owner through natural-language instructions to an AI coding
assistant, which proposed designs and wrote code. The owner reviewed the
changes in each PR and directed every merge - one merged by him directly, the
others executed by the assistant on his explicit instruction. The owner's
directives are quoted below (voice notes auto-transcribed; transcription
artifacts preserved, e.g. "Sawan" = Savaan). Elements the assistant proposed
rather than the owner are marked [assistant proposal].

1. Introducing the project: "I had built this project way back called Sawan,
   which was basically an emotion first kind of AI and it would drive
   conversations based on values of dopamine and survival that we are
   simulating based on a YAML file that has every emotion in it. So you write
   something, it gets emotionally tagged with one call and then it goes
   through the main LLM and we have three-tiered storage using ChromaDB...
   You think that sounds good?"
2. "Yeah, can you actually go and check my Sawan repo? It is public and it is
   there in my GitHub only, niranjan12s."
3. "Yeah, let's draft a plan for how we'll need to make this something that we
   can add to our Cloudflare, you know, form. What will we need exactly? Let's
   draft a cleanup list and a porting plan."
4. "When we say we have to port it to Cloudflare, what is the stack we are
   actually porting it to?"
5. The key design constraint: "Then I would not like the entire codebase to be
   replaced by it. I would say that let us have an interface and then I would
   want to wire this through an interface and it should be switchable where I
   can also keep my current behavior but also have it working with Cloudflare
   because why should I just replace my entire codebase for the sake of it,
   right? I would rather have it wired through an interface and then
   switchable."
6. "Yes, please update the design doc for the repo. Also, can you also open a
   PR and start working on it?"
7. "You can get started on... everything if you want, Cloudflare, the work as
   well... Or if you can write the implementations yourself, I'll just go
   through the PR."
8. "fix the bug" (directing repair of the episodic-memory write path found
   during his review)
9. "I see that all the implementation that you have done for Cloudflare
   adapters, all of them are in TypeScript. Is there a specific reason why all
   of them are in TypeScript or is it because Cloudflare only supports
   TypeScript?"
10. "Can you merge the open PRs in after merging main into them if they need a
    rebase and then merge both of them in? I'll have to look into how I can
    actually get this code running."
11. "okay merge it in and get it deployed if needdd"

Design elements proposed by the assistant (not the owner's prompts): the
specific four interfaces (LLM, vector store, state store, transcriber) and the
SAVAAN_STACK switch [assistant proposal in response to directive 5]; Durable
Object per-user emotion state, Vectorize + bge embeddings for memory, model
selection, TypeScript as the Worker language; the base64 audio fix for Workers
AI Whisper; the PR breakdown. The cleanup list, porting plan, and design doc
were assistant-drafted and owner-approved.

Coverage limits: this history covers the Nov 15-16 port, deployment and
debugging only; the original Python app was built earlier and outside this
record. Review questions, approvals and routine status exchanges are omitted.
The owner's hands-on frontend fixes on Nov 16 (removing dead template imports,
demo routing, microphone error handling) were made by him directly, guided by
chat diagnosis rather than code-generating prompts. This is a curated history
of the owner's directives, not a complete message log.
