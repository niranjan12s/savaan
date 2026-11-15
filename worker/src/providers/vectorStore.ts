// VectorStore for Cloudflare: Workers AI embeddings + Vectorize.
// Mirrors providers/vector_store.py (embed / add_episode / query_episodes).

export interface EpisodeMetadata {
  user_id: string;
  dopamine_user: number;
  survival_user: number;
  dopamine_ai: number;
  survival_ai: number;
  tags: string[];
  episodic_embedding: string;
  timestamp: string;
}

export interface VectorStore {
  embed(text: string): Promise<number[]>;
  addEpisode(
    episodeId: string,
    documents: string[],
    embedding: number[],
    metadata: EpisodeMetadata
  ): Promise<void>;
  queryEpisodes(
    embedding: number[],
    nResults?: number
  ): Promise<{ documents: string[][]; distances: number[][] }>;
}

export class VectorizeStore implements VectorStore {
  constructor(
    private ai: Ai,
    private index: VectorizeIndex,
    private embeddingModel = "@cf/baai/bge-base-en-v1.5"
  ) {}

  async embed(text: string): Promise<number[]> {
    const result = (await this.ai.run(this.embeddingModel, {
      text: [text],
    })) as { data: number[][] };
    return result.data[0];
  }

  async addEpisode(episodeId: string, documents: string[], embedding: number[], metadata: EpisodeMetadata) {
    // Vectorize stores one vector per id; the frames and summary travel in metadata.
    await this.index.upsert([
      {
        id: episodeId,
        values: embedding,
        metadata: { ...metadata, documents },
      },
    ]);
  }

  async queryEpisodes(embedding: number[], nResults = 5) {
    const matches = await this.index.query(embedding, {
      topK: nResults,
      returnMetadata: "all",
    });
    const documents: string[][] = [
      matches.matches.map(
        (m) => ((m.metadata as Record<string, unknown>)?.documents as string[])?.join("\n") ?? ""
      ),
    ];
    const distances: number[][] = [matches.matches.map((m) => 1 - m.score)];
    return { documents, distances };
  }
}
