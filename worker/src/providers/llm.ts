// LLMProvider for Cloudflare: Workers AI Llama 3.3.
// Mirrors providers/llm.py (LLMProvider.generate).

export interface LLMProvider {
  generate(prompt: string): Promise<string>;
}

export class WorkersAILLM implements LLMProvider {
  constructor(
    private ai: Ai,
    private model = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
  ) {}

  async generate(prompt: string): Promise<string> {
    const result = (await this.ai.run(this.model, {
      messages: [{ role: "user", content: prompt }],
    })) as { response?: string };
    return result.response ?? "";
  }
}
