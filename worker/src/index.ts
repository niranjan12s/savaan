// Thin Worker entrypoint: wiring + HTTP. The logic lives in pipeline.ts and
// the providers. Auth is intentionally absent: the demo talks to one user id
// and the Python service's JWT layer does not port (see PR description).

import { EmotionState } from "./durable/EmotionState";
import { respond, type Env } from "./pipeline";
import { WorkersAILLM } from "./providers/llm";
import { D1ConversationStore } from "./providers/stateStore";
import { WorkersAITranscriber } from "./providers/transcriber";
import { VectorizeStore } from "./providers/vectorStore";

export { EmotionState };

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const match = url.pathname.match(/^\/users\/([^/]+)\/respond$/);
    if (request.method !== "POST" || !match) {
      return json({ detail: "Not found" }, 404);
    }
    const userId = match[1];

    const form = await request.formData();
    const file = form.get("file");
    if (!(file instanceof File)) {
      return json({ detail: "Expected multipart form field 'file' with the audio" }, 400);
    }

    const id = env.EMOTION_STATE.idFromName(userId);
    const emotionState = env.EMOTION_STATE.get(id);

    try {
      const result = await respond(userId, await file.arrayBuffer(), {
        llm: new WorkersAILLM(env.AI),
        transcriber: new WorkersAITranscriber(env.AI),
        vectorStore: new VectorizeStore(env.AI, env.VECTORIZE),
        conversationStore: new D1ConversationStore(env.DB),
        emotionState,
      });
      return json(result);
    } catch (err) {
      console.error("respond failed", err);
      return json({ detail: "An error occured while processing the request" }, 500);
    }
  },
} satisfies ExportedHandler<Env>;
