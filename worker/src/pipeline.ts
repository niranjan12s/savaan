// The /respond pipeline on Cloudflare, mirroring savaan-service/main.py.
// Intent-preserving choices (flagged in the PR for review):
//  1. The Python episode condition compares a list to an int (history >= 10),
//     which raises TypeError in Python 3, so episodes were never created and
//     the endpoint 500s. Here it is implemented as len(history) >= 10.
//  2. The Python parse_episodic_memory (the function that actually stores the
//     episode) is never called; here the continuity-drop path creates AND
//     stores the episode in Vectorize.

import {
  buildEmotionTaggingPrompt,
  buildEpisodicEmbeddingPrompt,
  buildEpisodicMemoryPrompt,
  buildEpisodeProbePrompt,
  buildReplyPrompt,
  parseJsonResponse,
  type Metrics,
} from "./prompts";
import type { LLMProvider } from "./providers/llm";
import type { ConversationStateStore } from "./providers/stateStore";
import type { Transcriber } from "./providers/transcriber";
import type { VectorStore } from "./providers/vectorStore";

import type { EmotionState } from "./durable/EmotionState";

export interface Env {
  AI: Ai;
  VECTORIZE: VectorizeIndex;
  DB: D1Database;
  EMOTION_STATE: DurableObjectNamespace<EmotionState>;
}

// The subset of the Durable Object the pipeline calls, satisfied by the stub.
export interface EmotionStateClient {
  getCurrent(): Promise<Metrics>;
  getHistory(): Promise<import("./prompts").MetricsHistory>;
  recalculate(
    stimuliUser: Record<string, number>,
    stimuliAi: Record<string, number>
  ): Promise<Metrics>;
}

export interface PipelineDeps {
  llm: LLMProvider;
  transcriber: Transcriber;
  vectorStore: VectorStore;
  conversationStore: ConversationStateStore;
  emotionState: EmotionStateClient;
}

async function tagEmotions(
  text: string,
  llm: LLMProvider
): Promise<Record<string, number>> {
  try {
    return parseJsonResponse(await llm.generate(buildEmotionTaggingPrompt(text)));
  } catch {
    return {};
  }
}

export async function respond(
  userId: string,
  audio: ArrayBuffer,
  deps: PipelineDeps
): Promise<{ transcript: string; response: string; metrics: Metrics }> {
  const { llm, transcriber, vectorStore, conversationStore, emotionState } = deps;

  const transcript = await transcriber.transcribe(audio);

  const stimuliUser = await tagEmotions(transcript, llm);
  const currentMetrics = await emotionState.getCurrent();
  const history = await conversationStore.getConversationHistory(userId);

  // Episodic recall: probe built from the moment's emotional signature.
  const probe = buildEpisodeProbePrompt(
    stimuliUser,
    transcript,
    currentMetrics.dopamine_user,
    currentMetrics.survival_user,
    currentMetrics.dopamine_ai,
    currentMetrics.survival_ai,
    history ? JSON.stringify(history) : undefined
  );
  const episodic = await vectorStore.queryEpisodes(await vectorStore.embed(probe), 5);

  const metricsHistory = await emotionState.getHistory();
  const reply = parseJsonResponse<{ response: string; continuity: number }>(
    await llm.generate(
      buildReplyPrompt(transcript, currentMetrics, metricsHistory, history, episodic.documents)
    )
  );

  const stimuliAi = await tagEmotions(reply.response, llm);

  // Episode boundary: continuity dropped and the conversation is long enough.
  if (reply.continuity < 1 && history !== null && history.length >= 10) {
    const memory = parseJsonResponse<{ frames: string[]; tags: string[] }>(
      await llm.generate(buildEpisodicMemoryPrompt(history))
    );
    const summary = await llm.generate(
      buildEpisodicEmbeddingPrompt(memory.tags, metricsHistory, currentMetrics)
    );
    await vectorStore.addEpisode(crypto.randomUUID(), memory.frames, await vectorStore.embed(summary), {
      user_id: userId,
      dopamine_user: currentMetrics.dopamine_user,
      survival_user: currentMetrics.survival_user,
      dopamine_ai: currentMetrics.dopamine_ai,
      survival_ai: currentMetrics.survival_ai,
      tags: memory.tags,
      episodic_embedding: summary,
      timestamp: new Date().toISOString(),
    });
    await conversationStore.resetConversation(userId);
  }

  const metrics = await emotionState.recalculate(stimuliUser, stimuliAi);
  await conversationStore.updateConversationHistory(userId, "user", transcript, reply.continuity);
  await conversationStore.updateConversationHistory(userId, "ai", reply.response, reply.continuity);

  return { transcript, response: reply.response, metrics };
}
