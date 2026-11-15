// StateStore for Cloudflare: D1 holds conversation history.
// Mirrors providers/state_store.py for the conversation portion;
// dopamine/survival state lives in the EmotionState Durable Object.

export interface ConversationSnippet {
  role: string;
  text: string;
  continuity: number;
  timestamp: string;
}

export interface ConversationStateStore {
  getConversationHistory(userId: string): Promise<ConversationSnippet[] | null>;
  updateConversationHistory(
    userId: string,
    role: string,
    message: string,
    continuity: number
  ): Promise<void>;
  resetConversation(userId: string): Promise<void>;
}

export class D1ConversationStore implements ConversationStateStore {
  constructor(private db: D1Database) {}

  async getConversationHistory(userId: string) {
    const row = await this.db
      .prepare("SELECT messages FROM conversation_history WHERE user_id = ?")
      .bind(userId)
      .first<{ messages: string }>();
    if (!row) return null;
    return JSON.parse(row.messages) as ConversationSnippet[];
  }

  async updateConversationHistory(userId: string, role: string, message: string, continuity: number) {
    const snippet: ConversationSnippet = {
      role,
      text: message,
      continuity,
      timestamp: new Date().toISOString(),
    };
    const existing = await this.getConversationHistory(userId);
    const messages = existing ? [...existing, snippet] : [snippet];
    await this.db
      .prepare(
        `INSERT INTO conversation_history (user_id, messages) VALUES (?, ?)
         ON CONFLICT(user_id) DO UPDATE SET messages = excluded.messages`
      )
      .bind(userId, JSON.stringify(messages))
      .run();
  }

  async resetConversation(userId: string) {
    await this.db
      .prepare("UPDATE conversation_history SET messages = '[]' WHERE user_id = ?")
      .bind(userId)
      .run();
  }
}
